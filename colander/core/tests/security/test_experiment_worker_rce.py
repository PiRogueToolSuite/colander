"""Worker RCE + arbitrary write via a client-controlled artifact filename.

Source-driven PoC: it drives the real endpoints as an ordinary contributor and
lets the real worker task run.

    POST /upload -> /upload/<id>              (attacker-chosen name -> Artifact.name)
    POST /ws/<case>/collect/artifact   x3     PCAP (malicious) + SSLKEYLOG + SOCKET_T
    POST /ws/<case>/collect/experiment
    GET  /ws/<case>/collect/experiment/<id>/decrypt   -> experiment_to_har -> editcap (shell=True)

These assert the secure invariant, so a FAILING test means the vulnerability is present.
"""

import json
import os
import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from unittest import mock

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from colander.core.models import Artifact, ArtifactType, Case, PiRogueExperiment
from colander.core.tasks.experiment_to_har import ExperimentToHAR
from colander.core.utils import hash_file
from colander.users.models import User

_MEDIA_ROOT = tempfile.mkdtemp()


def _noop_task(*args, **kwargs):
    """Picklable stand-in for save_decrypted_traffic (django-q pickles tasks even in sync mode)."""


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
    MEDIA_ROOT=_MEDIA_ROOT,
)
class AuditWorkerInjectionPoC(TestCase):
    password = "8F7JbzWGES8hH4zWM6R1MPPCI5"
    RCE_MARKER = "RCE_PROOF"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="contributor", password=cls.password)
        cls.case = Case.objects.create(name="injection-case", owner=cls.user, description="poc")
        cls.t_pcap = ArtifactType.objects.create(short_name="PCAP", name="PCAP")
        cls.t_ssl = ArtifactType.objects.create(short_name="SSLKEYLOG", name="SSL keylog")
        cls.t_sock = ArtifactType.objects.create(short_name="SOCKET_T", name="Socket trace")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        self.client.login(username="contributor", password=self.password)

    def _upload(self, name, content):
        digest = hash_file(BytesIO(content))[0]
        init = self.client.post(
            reverse("initialize_upload"),
            data=json.dumps({"name": name, "size": len(content), "chunks": {"0": digest}}),
            content_type="application/json",
        )
        upload_id = init.json()["id"]
        self.client.post(
            reverse("append_to_upload", args=[upload_id]),
            data={"addr": 0, "file": SimpleUploadedFile("chunk", content)},
        )
        return upload_id

    def _make_artifact(self, artifact_type, name, content):
        upload_id = self._upload(name, content)
        self.client.post(
            reverse("collect_artifact_create_view", kwargs={"case_id": str(self.case.id)}),
            data={
                "type": str(artifact_type.id),
                "upload_request_ref": upload_id,
                "tlp": "WHITE",
                "pap": "WHITE",
            },
        )
        artifact = Artifact.objects.get(type=artifact_type, name=name, case=self.case)

        # Inline stand-in for the async hashing worker; makes the artifact selectable
        # in the experiment form without touching Artifact.name (the payload).
        artifact.file.save(f"{artifact.id}.bin", ContentFile(content), save=False)
        artifact.sha256, artifact.sha1, artifact.md5, _ = hash_file(BytesIO(content))
        artifact.save()
        return artifact

    def _create_experiment(self, pcap, sslkeylog, socket_trace):
        self.client.post(
            reverse("collect_experiment_create_view", kwargs={"case_id": str(self.case.id)}),
            data={
                "name": "experiment",
                "pcap": str(pcap.id),
                "sslkeylog": str(sslkeylog.id),
                "socket_trace": str(socket_trace.id),
                "tlp": "WHITE",
                "pap": "WHITE",
            },
        )
        return PiRogueExperiment.objects.get(name="experiment", case=self.case)

    def _write_stub_binaries(self, tooldir):
        editcap = tooldir / "editcap"
        tshark = tooldir / "tshark"
        editcap.write_text("#!/bin/sh\nexit 0\n")
        tshark.write_text("#!/bin/sh\nexit 0\n")
        editcap.chmod(0o755)
        tshark.chmod(0o755)
        return editcap, tshark

    def _trigger_decryption(self, experiment, cwd):
        url = reverse(
            "collect_experiment_decryption_view",
            kwargs={"case_id": str(self.case.id), "pk": str(experiment.id)},
        )
        tooldir = Path(tempfile.mkdtemp(prefix="worker-tools-"))
        self.addCleanup(shutil.rmtree, tooldir, ignore_errors=True)
        editcap, tshark = self._write_stub_binaries(tooldir)

        previous_cwd = os.getcwd()
        os.chdir(cwd)  # so the payload's relative `touch <marker>` lands here
        try:
            with mock.patch.object(ExperimentToHAR, "DEFAULT_EDITCAP_PATH", str(editcap)), \
                 mock.patch.object(ExperimentToHAR, "DEFAULT_TSHARK_PATH", str(tshark)), \
                 mock.patch.object(ExperimentToHAR, "generate_har", lambda self, har_path=None: None), \
                 mock.patch.object(ExperimentToHAR, "save_as_artifact", lambda self: None), \
                 mock.patch("colander.core.views.experiment_views.save_decrypted_traffic", _noop_task):
                self.client.get(url, HTTP_REFERER="http://testserver/")
        finally:
            os.chdir(previous_cwd)

    def test_editcap_path_executes_shell_metacharacters(self):
        # Slash-free so it survives generate_dump()'s open(output_dir / name) before editcap.
        pcap = self._make_artifact(self.t_pcap, f"evilx$(touch {self.RCE_MARKER}).pcap", b"PCAPDATA")
        ssl = self._make_artifact(self.t_ssl, "keys.txt", b"sslkeys")
        sock = self._make_artifact(self.t_sock, "socket.json", b"[]")
        experiment = self._create_experiment(pcap, ssl, sock)

        with tempfile.TemporaryDirectory() as workdir:
            self._trigger_decryption(experiment, cwd=workdir)
            self.assertFalse(
                (Path(workdir) / self.RCE_MARKER).exists(),
                "the uploaded filename executed a shell command on the worker",
            )

    def test_artifact_dump_escapes_output_directory(self):
        with tempfile.TemporaryDirectory() as escape_dir, tempfile.TemporaryDirectory() as workdir:
            escaped_file = Path(escape_dir) / "escaped.bin"
            pcap = self._make_artifact(self.t_pcap, str(escaped_file), b"audit-proof")
            ssl = self._make_artifact(self.t_ssl, "keys.txt", b"sslkeys")
            sock = self._make_artifact(self.t_sock, "socket.json", b"[]")
            experiment = self._create_experiment(pcap, ssl, sock)

            self._trigger_decryption(experiment, cwd=workdir)
            self.assertFalse(
                escaped_file.exists(),
                "uploaded bytes were written outside the worker's output directory",
            )
