# colander/core/tests/security/test_stored_xss.py
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from colander.core.models import Case, Observable, ObservableType
from colander.users.models import User


class AuditEntityNameXSSTest(TestCase):
    xss_payload = '<img src=x onerror=alert(1)>'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='relation-form-user')
        cls.case = Case.objects.create(
            name='Stored XSS test case',
            description='Case containing an entity with a hostile value',
            owner=cls.user,
        )
        observable_type = ObservableType.objects.create(short_name='XSS', name='XSS test observable')
        Observable.objects.create(
            name=cls.xss_payload,
            type=observable_type,
            owner=cls.user,
            case=cls.case,
        )

    def test_relation_creation_form_escapes_entity_value(self):
        self.client.force_login(self.user)

        def render_source_entity_field(_request, _template_name, context):
            return HttpResponse(context['form']['obj_from'].as_widget())

        with patch('colander.core.views.relation_views.render', side_effect=render_source_entity_field):
            response = self.client.get(
                reverse(
                    'collect_entity_relation_create_view',
                    kwargs={'case_id': str(self.case.id)},
                )
            )

        self.assertEqual(response.status_code, 200)
        response_html = response.content.decode()
        self.assertNotIn(self.xss_payload, response_html)
        self.assertIn(escape(self.xss_payload), response_html)
