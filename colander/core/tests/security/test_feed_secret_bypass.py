# colander/core/tests/security/test_feed_secret_bypass.py
from django.test import Client, TestCase
from django.urls import reverse
from colander.core.models import Case, EntityExportFeed
from colander.users.models import User

class TestFeedSecretBypass(TestCase):
    password = ['8F7JbzWGES8hH4zWM6R1MPPCI5', '8F7JbzWGES8hH4zWM6R1MPPCI6']

    @classmethod
    def setUpTestData(cls):
        # User 1
        cls.user_1 = User.objects.create_user(username='u1', password=cls.password[0])
        cls.case_1 = Case.objects.create(name='case 1', owner=cls.user_1, description='xx')
        cls.feed = EntityExportFeed.objects.create(
            name='private-feed',
            owner=cls.user_1,
            case=cls.case_1,
        )
        # User 2
        cls.user_2 = User.objects.create_user(username='u2', password=cls.password[1])
        cls.case_2 = Case.objects.create(name='case 2', owner=cls.user_2, description='xx')

    def _feed_url(self, feed):
        return reverse('entity_out_feed_view', kwargs={'pk': str(feed.id)})

    def test_unrelated_authenticated_user_cannot_read_foreign_feed(self):
        anon = Client().get(self._feed_url(self.feed), {'info': '1'})
        self.assertNotEqual(anon.status_code, 200, "anonymous no-secret access should be refused")

        attacker = Client()
        attacker.login(username=self.user_2.username, password=self.password[1])
        info = attacker.get(self._feed_url(self.feed), {'info': '1'})
        export = attacker.get(self._feed_url(self.feed), {'format': 'json'})
        self.assertNotIn('private-feed', info.content.decode(), "feed name disclosed")
        self.assertNotEqual(info.status_code, 200, "attacker read metadata without secret")
        self.assertNotEqual(export.status_code, 200, "attacker read feed export without secret")
