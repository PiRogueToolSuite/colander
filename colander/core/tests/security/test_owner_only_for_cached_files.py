import os
import tempfile
from django.test import TestCase, override_settings, Client
from django.urls import reverse

from colander.users.models import User

_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION": os.path.join(_MEDIA_ROOT, "cache"),
        },
    },
    DEBUG=False,
    MEDIA_ROOT=_MEDIA_ROOT,
)
class TestOwnerOnlyForCachedFile(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = ['8F7JbzWGES8hH4zWM6R1MPPCI7', '8F7JbzWGES8hH4zWM6R1MPPCI8']
        cls.user_1 = User.objects.create_user(username='user one', password=cls.password[0])
        cls.user_2 = User.objects.create_user(username='user two', password=cls.password[1])

    def test_owner_only_for_cached_file(self):
        client = Client()
        client.login(username='user one', password=self.password[0])

        cached_file_payload = {
            "content": "private content",
        }

        response = client.post(
            reverse('rest:cached_files'),
            cached_file_payload,
        )

        self.assertEqual(response.status_code, 201, "user can't upload CachedFile")
        json_response = response.json()
        self.assertEqual(json_response['status'], 'success', "upload CachedFile fail")
        cached_file_id = json_response['uuid']
        self.assertIsNotNone(cached_file_id, "upload CachedFile does not have uuid")

        response = client.get(
            reverse('rest:cached_file_detail', kwargs={'pk': cached_file_id})
        )
        self.assertEqual(response.status_code, 200, "user can't retrieve his CachedFile")
        self.assertContains(response, "private content")

        attacker = Client()
        attacker.login(username='user two', password=self.password[1])
        response = attacker.get(
            reverse('rest:cached_file_detail', kwargs={'pk': cached_file_id})
        )
        self.assertNotEqual(response.status_code, 200, "attacker can retrieve user CachedFile")

