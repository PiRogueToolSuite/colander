from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from colander.core.models import Artifact, ArtifactType, Case
from colander.users.models import User


@override_settings(
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.InMemoryStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class ArtifactInlineXSSRegressionTest(TestCase):
    xss_payload = b"<!doctype html><script>alert(document.domain)</script>"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="artifact-xss-user")
        cls.case = Case.objects.create(
            name="Artifact XSS regression case",
            description="Case containing a hostile HTML artifact",
            owner=cls.user,
        )

        cls.executable_media_types = {"text/html", "application/xhtml+xml", "image/svg+xml"}

        artifact_type = ArtifactType.objects.create(
            short_name="XSS_HTML",
            name="HTML XSS regression artifact",
        )
        cls.artifact_html = Artifact.objects.create(
            name="payload.html",
            original_name="payload.html",
            mime_type="text/html",
            file=SimpleUploadedFile(
                "payload.html",
                cls.xss_payload,
                content_type="text/html",
            ),
            type=artifact_type,
            owner=cls.user,
            case=cls.case,
        )
        cls.artifact_svg = Artifact.objects.create(
            name="payload.svg",
            original_name="payload.svg",
            mime_type="image/svg+xml",
            file=SimpleUploadedFile(
                "payload.svg",
                cls.xss_payload,
                content_type="image/svg+xml",
            ),
            type=artifact_type,
            owner=cls.user,
            case=cls.case,
        )

    def test_html_artifact_is_not_served_as_executable_inline_content(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "collect_artifact_view_view",
                kwargs={
                    "case_id": self.case.id,
                    "pk": self.artifact_html.id,
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        disposition = response.headers.get("Content-Disposition", "").lower()
        media_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
        self.assertFalse(
            disposition.startswith("inline") and media_type in self.executable_media_types,
            "The XSS payload is served as executable inline content on the Colander origin",
        )

    def test_svg_artifact_is_not_served_as_executable_inline_content(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "collect_artifact_view_view",
                kwargs={
                    "case_id": self.case.id,
                    "pk": self.artifact_svg.id,
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        disposition = response.headers.get("Content-Disposition", "").lower()
        media_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
        self.assertFalse(
            disposition.startswith("inline") and media_type in self.executable_media_types,
            "The XSS payload is served as executable inline content on the Colander origin",
        )
