import hashlib
import os
import tempfile
from io import StringIO

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
class TestUploadRequestPrivacy(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = ['8F7JbzWGES8hH4zWM6R1MPPCI9', '8F7JbzWGES8hH4zWM6R1MPPCIA']
        cls.user_1 = User.objects.create_user(username='other user one', password=cls.password[0])
        cls.user_2 = User.objects.create_user(username='other user two', password=cls.password[1])

    def test_restrict_upload_request_session_to_owner(self):
        client = Client()
        client.login(username='other user one', password=self.password[0])

        upload_request_file = StringIO("Private Content")
        upload_request_file_size = len(upload_request_file.getvalue().encode('utf-8'))
        upload_request_file_sha256 = hashlib.sha256(upload_request_file.getvalue().encode('utf-8')).hexdigest()

        upload_request_payload = {
            "name": "dummy-file-upload.txt",
            "size": upload_request_file_size,
            "chunks": {
                0: upload_request_file_sha256,
            },
        }

        response = client.post(
            reverse('initialize_upload'),
            upload_request_payload,
            "application/json",
        )

        self.assertEqual(response.status_code, 200, "user can't create upload request")
        json_response = response.json()
        self.assertEqual(json_response.get('status', None), 'CREATED', "upload CachedFile fail")
        upload_request_id = json_response.get('id', None)
        self.assertIsNotNone(upload_request_id, "upload request does not have id")

        response = client.get(
            reverse('append_to_upload', kwargs={'upload_id': upload_request_id})
        )
        self.assertEqual(response.status_code, 200, "user can't retrieve his upload request")
        json_response = response.json()
        self.assertEqual(json_response.get('status', None), 'CREATED', "upload CachedFile fail")

        attacker = Client()
        attacker.login(username='other user two', password=self.password[1])
        response = attacker.get(
            reverse('append_to_upload', kwargs={'upload_id': upload_request_id})
        )
        self.assertNotEqual(response.status_code, 200, "attacker can retrieve user upload request")
        self.assertTrue(response.status_code >= 400, "attacker exfiltrate data from user upload request")
        self.assertNotContains(response, "CREATED", response.status_code, "attacker exfiltrate data from user upload request")
