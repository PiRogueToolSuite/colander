# colander/core/tests/security/test_cross_tenant_idor.py
from django.test import Client, TestCase
from django.urls import reverse
from colander.core.models import (
    Actor,
    Artifact,
    Case,
    CustomExportFeed,
    DataFragment,
    Device,
    DeviceMonitoring,
    DetectionRule,
    DetectionRuleExportFeed,
    EntityExportFeed,
    EntityRelation,
    Event,
    FeedTemplate,
    PiRogueCredentials,
    PiRogueExperiment,
    SubGraph,
    Threat,
    Observable,
)
from colander.core.models import (
    ActorType,
    ArtifactType,
    DataFragmentType,
    DeviceType,
    DetectionRuleType,
    EventType,
    ThreatType,
    ObservableType,
)
from colander.users.models import User

class TestCrossTenantEntityIDOR(TestCase):
    password = ['8F7JbzWGES8hH4zWM6R1MPPCI5', '8F7JbzWGES8hH4zWM6R1MPPCI6']

    @classmethod
    def setUpTestData(cls):
        # User 1
        cls.user_1 = User.objects.create_user(username='u1', password=cls.password[0])
        cls.case_1 = Case.objects.create(name='case 1', owner=cls.user_1, description='xx')
        cls.device = Device.objects.create(
            name='case 1-laptop',
            description='xx',
            type=DeviceType.objects.create(short_name='LPT', name='laptop'),
            owner=cls.user_1,
            case=cls.case_1,
        )
        cls.pirogue_credential = PiRogueCredentials.objects.create(
            owner=cls.user_1,
            host="host.local",
            token="token 1",
            has_public_visibility=False,
        )
        # User 2
        cls.user_2 = User.objects.create_user(username='u2', password=cls.password[1])
        cls.case_2 = Case.objects.create(name='case 2', owner=cls.user_2, description='xx')

        cls.entities_tests_registry = [
            (
                Actor,
                "collect_actor_details_view",
                "collect_actor_delete_view",
                Actor.objects.create(
                    name='actor 1',
                    type=ActorType.objects.create(short_name='ACT', name='actor'),
                    owner=cls.user_1,
                    case=cls.case_1
                ),
            ),
            (
                Artifact,
                "collect_artifact_details_view",
                "collect_artifact_delete_view",
                Artifact.objects.create(
                    name='artifact 1',
                    type=ArtifactType.objects.create(short_name='ART', name='artifact'),
                    owner=cls.user_1,
                    case=cls.case_1,
                    original_name="original name 1"
                ),
            ),
            (
                DataFragment,
                "collect_data_fragment_details_view",
                "collect_data_fragment_delete_view",
                DataFragment.objects.create(
                    name='data fragment 1',
                    description='xx',
                    type=DataFragmentType.objects.create(short_name='DAF', name='data fragment'),
                    owner=cls.user_1,
                    case=cls.case_1,
                ),
            ),
            (
                DetectionRule,
                "collect_detection_rule_details_view",
                "collect_detection_rule_delete_view",
                DetectionRule.objects.create(
                    name='detection rule 1',
                    description='xx',
                    type=DetectionRuleType.objects.create(short_name='DER', name='detection rule'),
                    owner=cls.user_1,
                    case=cls.case_1,
                ),
            ),
            (
                Device,
                "collect_device_details_view",
                "collect_device_delete_view",
                Device.objects.create(
                    name='device 1',
                    description='xx',
                    type=DeviceType.objects.create(short_name='DEV', name='device'),
                    owner=cls.user_1,
                    case=cls.case_1,
                ),
            ),
            (
                Event,
                "collect_event_details_view",
                "collect_event_delete_view",
                Event.objects.create(
                    name='event 1',
                    type=EventType.objects.create(short_name='THR', name='event'),
                    owner=cls.user_1,
                    case=cls.case_1,
                ),
            ),
            (
                FeedTemplate,
                "feeds_template_live_editor_view",
                "feeds_template_delete_view",
                FeedTemplate.objects.create(
                    name='feed template 1',
                    owner=cls.user_1,
                    case=cls.case_1,
                    content='',
                ),
            ),
            (
                SubGraph,
                "subgraph_editor_view",
                "subgraph_delete_view",
                SubGraph.objects.create(
                    name='threat 1',
                    owner=cls.user_1,
                    case=cls.case_1,
                ),
            ),
            (
                Threat,
                "collect_threat_details_view",
                "collect_threat_delete_view",
                Threat.objects.create(
                    name='threat 1',
                    type=ThreatType.objects.create(short_name='THR', name='threat'),
                    owner=cls.user_1,
                    case=cls.case_1,
                ),
            ),
            (
                Observable,
                "collect_observable_details_view",
                "collect_observable_delete_view",
                Observable.objects.create(
                    name='observable 1',
                    type=ObservableType.objects.create(short_name='OBS', name='observable'),
                    owner=cls.user_1,
                    case=cls.case_1,
                ),
            ),
        ]
        cls.entities_tests_registry.extend([
            (
                CustomExportFeed,
                None,
                "feeds_custom_out_feed_delete_view",
                CustomExportFeed.objects.create(
                    name='custom export feed 1',
                    owner=cls.user_1,
                    case=cls.case_1,
                    template=cls.entities_tests_registry[6][3]
                ),
            ),
            (
                DetectionRuleExportFeed,
                None,
                "feeds_detection_rule_out_feed_delete_view",
                DetectionRuleExportFeed.objects.create(
                    name='detection rule export feed 1',
                    description='xx',
                    content_type=cls.entities_tests_registry[3][3].type,
                    owner=cls.user_1,
                    case=cls.case_1,
                ),
            ),
            (
                DeviceMonitoring,
                "device_monitoring_details_view",
                "device_monitoring_delete_view",
                DeviceMonitoring.objects.create(
                    description='xx',
                    owner=cls.user_1,
                    case=cls.case_1,
                    device=cls.entities_tests_registry[4][3],
                    pirogue=cls.pirogue_credential,
                ),
            ),
            (
                PiRogueExperiment,
                "collect_experiment_details_view",
                "collect_experiment_delete_view",
                PiRogueExperiment.objects.create(
                    name='experiment 1',
                    owner=cls.user_1,
                    case=cls.case_1,
                    pcap=cls.entities_tests_registry[1][3],
                    socket_trace=cls.entities_tests_registry[1][3],
                    sslkeylog=cls.entities_tests_registry[1][3],
                ),
            ),
            (
                EntityExportFeed,
                None,
                "feeds_entity_out_feed_delete_view",
                EntityExportFeed.objects.create(
                    name='detection rule export feed 1',
                    description='xx',
                    owner=cls.user_1,
                    case=cls.case_1,
                ),
            ),
            (
                EntityRelation,
                None,
                "collect_entity_relation_delete_view",
                EntityRelation.objects.create(
                    name='related to',
                    owner=cls.user_1,
                    case=cls.case_1,
                    obj_from=cls.entities_tests_registry[1][3],
                    obj_to=cls.entities_tests_registry[2][3],
                ),
            ),
        ])

    def _view_url(self, view_name, case, entity):
        return reverse(view_name,
                       kwargs={'case_id': str(case.id), 'pk': str(entity.id)})

    def test_attacker_read_and_delete_foreign_device(self):
        attacker = Client()
        attacker.login(username=self.user_2.username, password=self.password[1])

        response = attacker.get(self._view_url('collect_device_details_view', self.case_1, self.device))
        self.assertNotEqual(response.status_code, 200, "attacker has access")

        # Cross case workspace
        read = attacker.get(self._view_url('collect_device_details_view', self.case_2, self.device))
        delete = attacker.get(self._view_url('collect_device_delete_view', self.case_2, self.device))

        self.assertNotEqual(read.status_code, 200, "IDOR: u2 read u1's device")
        self.assertNotContains(read, 'case 1-laptop', status_code=read.status_code,
                               msg_prefix="IDOR: u2 read u1's device")
        self.assertNotEqual(delete.status_code, 200, "IDOR: u2 deleted u1's device")
        self.assertTrue(Device.objects.filter(id=self.device.id).exists(), "deleted cross-tenant")

        # External case access
        read = attacker.get(self._view_url('collect_device_details_view', self.case_1, self.device))
        delete = attacker.get(self._view_url('collect_device_delete_view', self.case_1, self.device))

        self.assertNotEqual(read.status_code, 200, "IDOR: u2 read u1's device")
        self.assertNotContains(read, 'case 1-laptop', status_code=read.status_code,
                               msg_prefix="IDOR: u2 read u1's device")
        self.assertNotEqual(delete.status_code, 200, "IDOR: u2 deleted u1's device")
        self.assertTrue(Device.objects.filter(id=self.device.id).exists(), "deleted cross-tenant")

    def test_attacker_read_delete_foreign_pirogue_credential(self):
        owner = Client()
        owner.login(username=self.user_1.username, password=self.password[0])
        attacker = Client()
        attacker.login(username=self.user_2.username, password=self.password[1])

        self.assertTrue(PiRogueCredentials.objects.filter(id=self.pirogue_credential.id).exists(),
                        "entity does not exist")

        detail_view_url = reverse("pirogue_credentials_details_view",
                                  kwargs={'pk': str(self.pirogue_credential.id)})

        response = owner.get(detail_view_url)
        self.assertEqual(response.status_code, 200, "owner pirogue_credential does not exist")

        response = attacker.get(detail_view_url)
        self.assertNotEqual(response.status_code, 200, "attacker has access")

        delete_view_url = reverse("pirogue_credentials_delete_view",
                                  kwargs={'pk': str(self.pirogue_credential.id)})
        response = attacker.get(delete_view_url)
        self.assertNotEqual(response.status_code, 200, "attacker can delete")
        self.assertTrue(PiRogueCredentials.objects.filter(id=self.pirogue_credential.id).exists(),
                        "attacker has deleted pirogue_credential")

    def test_attacker_read_delete_foreign_entities(self):
        owner = Client()
        owner.login(username=self.user_1.username, password=self.password[0])
        attacker = Client()
        attacker.login(username=self.user_2.username, password=self.password[1])

        for test_reg in self.entities_tests_registry:
            print(f"test_attacker_read_delete_foreign_entities[{test_reg[0]}] ...")
            self.assertTrue(test_reg[0].objects.filter(id=test_reg[3].id).exists(),
                            "entity does not exist")

            if test_reg[1]: # Detail view may not exist
                response = owner.get(self._view_url(test_reg[1], self.case_1, test_reg[3]))
                self.assertEqual(response.status_code, 200, "owner entity does not exist")

                # Through owner case
                response = attacker.get(self._view_url(test_reg[1], self.case_1, test_reg[3]))
                self.assertNotEqual(response.status_code, 200, "attacker has access")

                # Through attacker case
                response = attacker.get(self._view_url(test_reg[1], self.case_2, test_reg[3]))
                self.assertNotEqual(response.status_code, 200, "IDOR: attacker read entity")

            # Delete access
            response = attacker.get(self._view_url(test_reg[2], self.case_1, test_reg[3]))
            self.assertNotEqual(response.status_code, 200, "attacker can delete")
            self.assertTrue(test_reg[0].objects.filter(id=test_reg[3].id).exists(),
                            "attacker has deleted entity")

            # IDOR Delete access
            response = attacker.get(self._view_url(test_reg[2], self.case_2, test_reg[3]))
            self.assertNotEqual(response.status_code, 200, "IDOR: attacker can delete")
            self.assertTrue(test_reg[0].objects.filter(id=test_reg[3].id).exists(),
                            "IDOR: attacker has deleted entity")

