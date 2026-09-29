from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings

from colander.core.models import Case, Observable, ObservableType, ArtifactType
from colander.core.observable_tasks import capture_url
from colander.users.models import User


@override_settings(
    USE_PLAYWRIGHT=True,
)
class URLCaptureSSRFRegressionTest(TestCase):
    internal_url = "http://elasticsearch:9200/_cluster/health"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="url-capture-ssrf-user")
        cls.case = Case.objects.create(
            name="URL capture SSRF regression case",
            description="Case containing an internal URL observable",
            owner=cls.user,
        )
        observable_type = ObservableType.objects.create(
            short_name="URL",
            name="URL",
        )
        cls.observable = Observable.objects.create(
            name=cls.internal_url,
            type=observable_type,
            owner=cls.user,
            case=cls.case,
        )
        image_artifact_type = ArtifactType.objects.create(
            short_name="IMAGE",
            name="IMAGE",
        )
        har_artifact_type = ArtifactType.objects.create(
            short_name="HAR",
            name="HAR",
        )

    @patch("colander.core.observable_tasks.requests.post")
    def test_internal_url_is_rejected_before_playwright_request(self, playwright_post):
        playwright_post.return_value = SimpleNamespace(status_code=502)

        capture_url(self.observable.id)

        playwright_post.assert_not_called()
