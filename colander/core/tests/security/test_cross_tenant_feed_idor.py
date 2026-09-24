# colander/core/tests/security/test_cross_tenant_feed_idor.py
import json
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase
from django.urls import reverse
from colander.core.models import Actor, Case, EntityExportFeed, Threat, ThreatType
from colander.users.models import User

class TestCrossTenantFeedIDOR(TestCase):
    password = ['8F7JbzWGES8hH4zWM6R1MPPCI5', '8F7JbzWGES8hH4zWM6R1MPPCI6']

    @classmethod
    def setUpTestData(cls):
        # User 1
        cls.user_1 = User.objects.create_user(username='u1', password=cls.password[0])
        cls.case_1 = Case.objects.create(name='case 1', owner=cls.user_1, description='xx')
        cls.threat_type = ThreatType.objects.create(short_name='ADWARE', name='adware')
        cls.threat = Threat.objects.create(
            name='red_adware',
            type=cls.threat_type,
            owner=cls.user_1,
            case=cls.case_1,
            tlp='RED',
            pap='WHITE',
        )
        # User 2
        cls.user_2 = User.objects.create_user(username='u2', password=cls.password[1])
        cls.case_2 = Case.objects.create(name='case 2', owner=cls.user_2, description='xx')

    def _create_url(self, case):
        return reverse('feeds_entity_out_feed_create_view',
                       kwargs={'case_id': str(case.id)})

    def _edit_url(self, case, feed):
        return reverse('feeds_entity_out_feed_update_view',
                       kwargs={'case_id': str(case.id), 'pk': str(feed.id)})

    def _feed_url(self, feed):
        return reverse('entity_out_feed_view', kwargs={'pk': str(feed.id)})

    def test_attacker_widens_foreign_feed_to_exfiltrate_red_threat(self):
        actor_ct = ContentType.objects.get_for_model(Actor)
        threat_ct = ContentType.objects.get_for_model(Threat)

        victim = Client()
        victim.login(username=self.user_1.username, password=self.password[0])
        # narrow feed: Actors only, capped at TLP:WHITE.
        u1_secret = 'u1-original-secret'
        create = victim.post(self._create_url(self.case_1), {
            'name': 'u1 actors feed',
            'description': 'xx',
            'secret': u1_secret,
            'max_tlp': 'WHITE',
            'max_pap': 'WHITE',
            'content_type': [str(actor_ct.pk)],
        })
        feed = EntityExportFeed.objects.get(name='u1 actors feed')

        attacker = Client()
        attacker.login(username=self.user_2.username, password=self.password[1])
        attacker_secret = 'attacker-controlled-secret'
        edit = attacker.post(self._edit_url(self.case_2, feed), {
            'name': 'u1 actors feed',
            'description': 'pwned',
            'secret': attacker_secret,
            'max_tlp': 'RED',                     # <-- widen TLP
            'max_pap': 'WHITE',
            'content_type': [str(threat_ct.pk)],  # <-- Threat export
        })
        self.assertNotEqual(edit.status_code, 200, "attacker can edit feed")
        feed.refresh_from_db()

        not_leaked = Client().get(self._feed_url(feed), {'secret': attacker_secret})
        self.assertNotEqual(not_leaked.status_code, 200, "attacker has changed feed secret")

        still_secured = Client().get(self._feed_url(feed), {'secret': u1_secret})
        exported = list(json.loads(still_secured.content).get('entities', {}).values())

        self.assertNotIn('red_adware', [e.get('name') for e in exported], "exfiltrated adware")
        self.assertEqual(feed.max_tlp, 'WHITE', "attacker raised max_tlp")
        self.assertNotIn(threat_ct, list(feed.content_type.all()),
                      "attacker added the Threat content type to the feed")
        self.assertNotEqual(feed.secret, attacker_secret, "attacker changed secret")
