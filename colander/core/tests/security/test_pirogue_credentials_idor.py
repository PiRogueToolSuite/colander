# colander/core/tests/security/test_pirogue_credentials_idor.py
from django.test import Client, TestCase
from django.urls import reverse
from colander.core.models import PiRogueCredentials
from colander.users.models import User

class PiRogueCredentialsIDORTest(TestCase):
    VICTIM_TOKEN = 'VICTIM-SECRET-TOKEN-do-not-leak-0123456789'

    @classmethod
    def setUpTestData(cls):
        cls.password = ['8F7JbzWGES8hH4zWM6R1MPPCI7', '8F7JbzWGES8hH4zWM6R1MPPCI8']
        cls.user_1 = User.objects.create_user(username='u1', password=cls.password[0])
        cls.pi_cred = PiRogueCredentials.objects.create(
            owner=cls.user_1, friendly_name='pirogue',
            host='victim-pirogue.internal', port=50051,
            token=cls.VICTIM_TOKEN, has_public_visibility=True,
        )
        cls.user_2 = User.objects.create_user(username='u2', password=cls.password[1])

    def test_attacker_exfiltrates_token_via_edit_view(self):
        attacker = Client()
        attacker.login(username=self.user_2.username, password=self.password[1])
        edit_url = reverse('pirogue_credentials_update_view', kwargs={'pk': str(self.pi_cred.id)})
        resp = attacker.get(edit_url)

        # these assert secure behavior; on the current code they fail
        self.assertNotIn(self.VICTIM_TOKEN, resp.content.decode(errors='ignore'))
        self.assertIn(resp.status_code, (403, 404))
