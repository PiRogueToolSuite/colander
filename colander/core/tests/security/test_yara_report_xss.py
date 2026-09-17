from types import SimpleNamespace
from unittest.mock import PropertyMock, patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from colander.core.models import (
    Artifact,
    ArtifactType,
    Case,
    DetectionRule,
    DetectionRuleType,
    PiRogueExperiment,
    PiRogueExperimentAnalysis,
)
from colander.core.tasks.experiment_tasks import _extract_matching_snippet
from colander.users.models import User


class AuditYARAReportXSSTest(TestCase):
    xss_payload = '<img src=x onerror=alert(1)>'
    yara_marker = 'VF1104_XSS_MARKER'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='yara-xss-regression-user')
        cls.case = Case.objects.create(
            name='YARA report XSS regression case',
            description='Case containing the YARA report regression test',
            owner=cls.user,
        )

        artifact_type = ArtifactType.objects.create(
            short_name='XSS_PCAP',
            name='XSS regression capture',
        )
        artifact = Artifact.objects.create(
            name='xss-regression.pcap',
            original_name='xss-regression.pcap',
            type=artifact_type,
            owner=cls.user,
            case=cls.case,
        )

        rule_type = DetectionRuleType.objects.create(
            short_name='XSS_YARA',
            name='XSS regression YARA rule',
        )
        cls.rule = DetectionRule.objects.create(
            name='XSS regression rule',
            type=rule_type,
            content=(
                'rule xss_regression { strings: '
                '$marker = "VF1104_XSS_MARKER" condition: $marker }'
            ),
            owner=cls.user,
            case=cls.case,
        )
        cls.experiment = PiRogueExperiment.objects.create(
            name='YARA report XSS regression experiment',
            pcap=artifact,
            socket_trace=artifact,
            sslkeylog=artifact,
            owner=cls.user,
            case=cls.case,
        )

    def test_analysis_report_sanitizes_yara_match_context(self):
        self.client.force_login(self.user)
        matched_content = self.yara_marker + self.xss_payload
        match = SimpleNamespace(
            offset=0,
            matched_length=len(self.yara_marker),
        )
        snippet = _extract_matching_snippet(match, matched_content)
        now = timezone.now()
        geoip = {
            'asn': {
                'asn': 0,
                'ip': '127.0.0.1',
                'network': '127.0.0.0/8',
                'organization_name': 'XSS regression test',
            },
            'country_name': 'Local',
            'country_iso_code': 'DE',
            'continent_name': 'Local',
        }
        analysis = PiRogueExperimentAnalysis(
            timestamp=now,
            decoded_data=matched_content,
            detections={
                'yara': [
                    {
                        'rule_id': str(self.rule.id),
                        'rule': 'xss_regression',
                        'tags': [],
                        'strings': [
                            {
                                'identifier': '$marker',
                                'instances': [snippet],
                            }
                        ],
                    }
                ]
            },
            result={
                'direction': 'outbound',
                'protocol': 'HTTP',
                'length': len(matched_content),
                'community_id': 'xss-regression-flow',
                'timestamp': int(now.timestamp() * 1000),
                'src': {
                    'ip': '127.0.0.1',
                    'host': 'source.test',
                    'geoip': geoip,
                },
                'dst': {
                    'ip': '127.0.0.1',
                    'host': 'destination.test',
                    'geoip': geoip,
                },
                'headers': [],
                'data': matched_content,
                'raw_data': matched_content,
                'stack_trace': [],
                'full_stack_trace': {
                    'process': 'xss-regression',
                    'pid': 0,
                    'data': {
                        'thread_id': 0,
                        'socket_fd': 0,
                        'stack': [],
                    },
                },
                'aes_info': {},
            },
        )

        with patch.object(
            PiRogueExperiment,
            'analysis',
            new_callable=PropertyMock,
            return_value=[analysis],
        ):
            response = self.client.get(
                reverse(
                    'collect_experiment_analysis_report_view',
                    kwargs={
                        'case_id': self.case.id,
                        'pk': self.experiment.id,
                    },
                )
            )

        self.assertNotContains(
            response,
            self.xss_payload,
            status_code=200,
        )
