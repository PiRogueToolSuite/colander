import logging
import platform
import subprocess
import tempfile
from pathlib import Path

from django.core.files import File
from pcapng_utils.pcapng_to_har import pcapng_to_har
from pcapng_utils.tshark import Tshark

from colander.core.models import Artifact, PiRogueExperiment, ArtifactType
from colander.core.utils import hash_file

logger = logging.getLogger(__name__)


class ArtifactDump:
    """
    A utility class to handle the dumping of an artifact into a specified output directory with optional overrides for
    filename and forceful override capabilities.

    This class allows users to specify whether to override the default filename or to enforce the recreation of the
    file in case it already exists, providing flexibility in managing storage scenarios.
    """

    def __init__(self, artifact: Artifact, output_directory: Path):
        self.artifact = artifact
        self.output_directory = output_directory
        self.dumped = False
        self.force_override = False
        self.filename_override: str | None = None

    @property
    def path(self) -> Path:
        if self.force_override:
            return self.output_directory / self.filename_override
        assert self.artifact is not None
        return self.output_directory / self.artifact.name

    @property
    def filename(self) -> str:
        if self.force_override:
            return self.filename_override
        assert self.artifact is not None
        return self.artifact.name

    @property
    def artifact_exists(self) -> bool:
        return bool(self.artifact)

    @property
    def exists(self) -> bool:
        return self.artifact_exists and self.path.is_file()

    def dump(self, force: bool = False, default_content: str | None = None, filename: str = None) -> 'ArtifactDump':
        """
        Dumps the artifact to a file.

        Parameters:
            force (bool): Whether to force override the existing artifact if it exists. Default is False.
            default_content (str | None): The content to use when forcing an override or creating a new artifact. Must be provided if `force` is True and no filename is given.
            filename (str): The name of the file where the artifact will be dumped. Required if `force` is True, otherwise ignored.

        Returns:
            ArtifactDump: The current instance after dumping the artifact.
        """
        if force and not self.artifact_exists:
            assert not self.exists, "The artifact does not exist but force is set to True."
            assert filename is not None, "Filename must be provided when forcing override."
            assert default_content is not None, "Default content must be provided when forcing override."

            self.force_override = True
            self.filename_override = filename
            output_path = self.output_directory / filename
            with output_path.open(mode='w') as f:
                f.write(default_content)
            self.dumped = True
        elif not self.artifact_exists:
            self.dumped = False
        elif self.exists:
            self.dumped = True
        else:
            with self.path.open(mode='wb') as f:
                for chunk in self.artifact.file.chunks():
                    f.write(chunk)
            self.dumped = True
        return self


class ExperimentDump:
    """
    Handle and processes artifacts from a PiRogueExperiment.

    This class encapsulates methods to interact with different types of experiment data such as PCAP files, SSL keylogs,
    socket traces, and AES trace information. It initializes by taking an instance of `PiRogueExperiment` and a
    directory path (`Path`) where the output should be saved. The artifacts are then processed into specific dump
    formats within this directory.

    Args:
        experiment (PiRogueExperiment): An instance of PiRogueExperiment containing necessary data files.
        output_directory (Path): A path-like object representing the directory where the generated dumps will be stored.

    Attributes:
        experiment (PiRogueExperiment): The experiment object containing raw data files.
        output_directory (Path): The directory where all artifact dump files are saved.
        pcap (ArtifactDump): An ArtifactDump instance for the PCAP file.
        ssl_keylog (ArtifactDump): An ArtifactDump instance for the SSL keylog file.
        socket_trace (ArtifactDump): An ArtifactDump instance for the socket trace file.
        aes_trace (ArtifactDump): An ArtifactDump instance for the AES trace file.
    """

    def __init__(self, experiment: PiRogueExperiment, output_directory: Path):
        self.experiment: PiRogueExperiment = experiment
        self.output_directory: Path = output_directory
        self.pcap: ArtifactDump = ArtifactDump(self.experiment.pcap, self.output_directory)
        self.ssl_keylog: ArtifactDump = ArtifactDump(self.experiment.sslkeylog, self.output_directory)
        self.socket_trace: ArtifactDump = ArtifactDump(self.experiment.socket_trace, self.output_directory)
        self.aes_trace: ArtifactDump = ArtifactDump(self.experiment.aes_trace, self.output_directory)
        assert self.pcap.artifact_exists is not None
        assert self.output_directory is not None and self.output_directory.is_dir()

    def generate_dump(self):
        self.pcap.dump()
        self.ssl_keylog.dump(force=True, filename='sslkeylog.txt', default_content='')
        self.socket_trace.dump(force=True, filename='socket_trace.json', default_content='[]')
        self.aes_trace.dump(force=True, filename='aes_info.jsont', default_content='[]')


class HARGenerationException(Exception):
    pass


class ExperimentToHAR:
    """
    Handles the generation of HAR (HTTP Archive) files from a PiRogueExperiment
    by processing captured network traffic.

    The class utilizes tools like TShark and EditCap to process network traffic
    dumps and inject necessary information (like secrets) to generate HTTP Archives.
    It automates the orchestration of these tools to simplify the process of extracting
    and converting experiment-related network traffic into a usable HAR file.

    Attributes:
        experiment (PiRogueExperiment): The experiment instance containing the network data needed to generate the HAR file.
        tshark_path (str): Path to the TShark executable.
        editcap_path (str): Path to the EditCap executable.
        pcapng_file_name (str): Name of the PCAPNG file to temporarily store captured traffic data.
        pcapng_path (Path or None): Path to the generated PCAPNG file in the temporary directory.
        har_file_name (str): Name of the HAR file to be generated.
        har_path (Path or None): Path to the generated HAR file in the temporary directory.
        experiment_dump (ExperimentDump or None): Represents the dumped experiment, including the required metadata and traffic logs.
    """

    DEFAULT_EDITCAP_PATH = {
        "Linux": "/usr/bin/editcap",
        "Darwin": "/Applications/Wireshark.app/Contents/MacOS/editcap",
    }.get(platform.system())
    DEFAULT_TSHARK_PATH = {
        "Linux": "/usr/bin/tshark",
        "Darwin": "/Applications/Wireshark.app/Contents/MacOS/tshark",
    }.get(platform.system())

    def __init__(self, experiment: PiRogueExperiment, tshark_path: str | None = None, editcap_path: str | None = None):
        self.experiment: PiRogueExperiment = experiment
        self.tshark_path: str = tshark_path or self.DEFAULT_TSHARK_PATH
        self.editcap_path: str = editcap_path or self.DEFAULT_EDITCAP_PATH
        self.pcapng_file_name: str = 'traffic.pcapng'
        self.pcapng_path: Path | None = None
        self.har_file_name: str = 'traffic.har'
        self.har_path: Path | None = None
        self.experiment_dump: ExperimentDump | None = None
        assert experiment is not None, "Experiment must be provided."
        assert self.tshark_path is not None and Path(
            self.tshark_path).exists(), f"TShark path {self.tshark_path} does not exist."
        assert self.editcap_path is not None and Path(
            self.editcap_path).exists(), f"EditCap path {self.editcap_path} does not exist."

    def _call_editcap(self):
        subprocess.check_call(
            f'{self.editcap_path} --inject-secrets tls,'
            f'{self.experiment_dump.ssl_keylog.path} '
            f'{self.experiment_dump.pcap.path} '
            f'{self.pcapng_path}',
            shell=True
        )

    def inject_secrets(self):
        """
        Inject TLS secrets into a network traffic capture file using editcap utility.

        This method uses the editcap tool to inject TLS secrets from a provided SSL
        keylog file into a PCAP file, generating a new PCAPNG file. The method ensures
        TLS secrets are correctly associated with the network traffic for further
        processing. In case of failure, an exception is raised and the error is logged.

        Raises:
            HARGenerationException: If the injection of secrets fails.
        """
        try:
            self._call_editcap()
        except Exception as e:
            logger.error(e)
            raise HARGenerationException(f'Failed to inject secrets for the experiment [{self.experiment.id}]')

    def generate_har(self, har_path: Path | None = None):
        """
        Generate an HTTP Archive (HAR) from a given PCAPNG file.

        This method uses the Tshark tool to convert a specified PCAPNG file into
        a HAR file, which is a format for recording web activity data. The input
        PCAPNG file can be processed to produce a HAR file that can be useful
        for analyzing HTTP traffic.

        Parameters:
            har_path (Path | None): Path to the generated HAR file in the output directory.

        Raises:
            HARGenerationException: Raised if the HAR generation process fails for the given PCAPNG file associated
                with the current experiment. The underlying reason is logged, and a descriptive error is raised.
        """
        _tshark = Tshark(tshark_cmd=self.tshark_path)
        try:
            pcapng_to_har(
                input_file=self.pcapng_path,
                output_file=har_path or self.har_path,
                tshark=_tshark,
                overwrite=True,
            )
        except Exception as e:
            logger.error(e)
            raise HARGenerationException(f'Failed to generate HAR for experiment [{self.experiment.id}]')

    def save_as_artifact(self) -> Artifact:
        """
        Saves the HAR file as an artifact associated with an experiment.

        The method generates a new artifact from the HAR file, calculates its hash
        values (SHA-256, SHA-1, MD5), and other metadata like size. The artifact is
        then persisted in the database and linked to the current experiment. This
        method ensures that the HAR file is stored securely and is accessible via
        its associated artifact.

        Returns:
            Artifact: The created artifact object representing the saved HAR file.

        Raises:
            None
        """
        with self.har_path.open('rb') as f:
            sha256, sha1, md5, size = hash_file(f)
        har_artifact = Artifact(
            name=f'{self.experiment.name} - {self.har_file_name}',
            type=ArtifactType.get_by_short_name('HAR'),
            case=self.experiment.case,
            owner=self.experiment.owner,
            file=File(file=self.har_path.open('rb'), name=self.har_file_name),
            original_name=self.har_file_name,
            mime_type='application/json',
            sha256=sha256,
            sha1=sha1,
            md5=md5,
            size_in_bytes=size,
            description=f'Automatically generated HAR file based on data collected during experiment '
                        f'{self.experiment.name}',
        )
        har_artifact.save()
        self.experiment.extra_files.add(har_artifact)
        self.experiment.save()
        return har_artifact

    def save(self, har_path: Path | None = None):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            self.pcapng_path = tmp_dir_path / self.pcapng_file_name
            self.har_path = har_path or tmp_dir_path / self.har_file_name
            self.experiment_dump = ExperimentDump(self.experiment, tmp_dir_path)
            self.experiment_dump.generate_dump()
            self.inject_secrets()
            self.generate_har(har_path)
            self.save_as_artifact()


def experiment_to_har(experiment_id: str):
    experiment = PiRogueExperiment.objects.get(id=experiment_id)
    eth = ExperimentToHAR(experiment)
    eth.save()
