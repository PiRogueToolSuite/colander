from django.test import TestCase, Client
from django.urls import reverse

from colander.core.models import Case, ColanderTeam
from colander.users.models import User


class TestCaseTeam(TestCase):
    password = '8F7JbzWGES8hH4zWM6R1MPPCI5'

    @classmethod
    def setUpTestData(cls):
        # User 1
        cls.user_1 = User.objects.create_user(username='u1', password=cls.password)
        cls.case_1 = Case.objects.create(name='case 1', owner=cls.user_1, description='xx')
        cls.team_1 = ColanderTeam.objects.create(name='t1', owner=cls.user_1)
        # User 2
        cls.user_2 = User.objects.create_user(username='u2', password=cls.password)
        cls.case_2 = Case.objects.create(name='case 2', owner=cls.user_2, description='xx')
        cls.team_2 = ColanderTeam.objects.create(name='t2', owner=cls.user_2)

    def test_case_management(self):
        c1 = Client()
        login1 = c1.login(username=self.user_1.username, password=self.password)
        self.assertTrue(login1, "User can login")

        # User can't add a case they don't own to their team
        response = c1.post(reverse('case_update_view', kwargs={'pk': str(self.case_2.id)}),
                           {
                               'name': self.case_2.name,
                               'description': 'yy',
                               'owner': self.user_2,
                               'tlp': self.case_2.tlp,
                               'pap': self.case_2.pap,
                               'teams': [str(self.team_1.id)]})
        self.assertEqual(response.status_code, 403, "User can't add a case they don't own to their team")

        # User can't add a case they don't own to a team they don't own
        response = c1.post(reverse('case_update_view', kwargs={'pk': str(self.case_2.id)}),
                           {
                               'name': self.case_2.name,
                               'description': 'zz',
                               'owner': self.user_2,
                               'tlp': self.case_2.tlp,
                               'pap': self.case_2.pap,
                               'teams': [str(self.team_2.id)]})
        self.assertEqual(response.status_code, 403, "User can't add a case they don't own to a team they don't own")

        # User can't add their case to a team they don't own
        response = c1.post(reverse('case_update_view', kwargs={'pk': str(self.case_1.id)}),
                           {
                               'name': self.case_1.name,
                               'description': 'yy',
                               'owner': self.user_1,
                               'tlp': self.case_1.tlp,
                               'pap': self.case_1.pap,
                               'teams': [str(self.team_2.id)]})
        self.assertEqual(response.status_code, 200, "User can't add their case to a team they don't own")
        case = Case.objects.get(id=self.case_1.id)
        self.assertFalse(self.team_2 in case.teams.all(), "User can't add their case to a team they don't own")

        # User can add their case to a team they own
        response = c1.post(reverse('case_update_view', kwargs={'pk': str(self.case_1.id)}),
                           data={
                               'name': self.case_1.name,
                               'description': 'zz',
                               'owner': self.user_1,
                               'tlp': self.case_1.tlp,
                               'pap': self.case_1.pap,
                               'teams': str(self.team_1.id)})
        self.assertEqual(response.status_code, 302, "User can add their case to a team they own")
        case = Case.objects.get(id=self.case_1.id)
        self.assertTrue(self.team_1 in case.teams.all(), "User can add their case to a team they own")

    def test_team_edition(self):
        c1 = Client()
        login1 = c1.login(username=self.user_1.username, password=self.password)
        self.assertTrue(login1, "User can login")

        # User can't add themselves to a team they don't own
        response = c1.post(reverse('collaborate_team_update_view', kwargs={'pk': str(self.team_2.id)}),
                           {'contributors': str(self.user_1.id)})
        self.assertEqual(response.status_code, 403, "User can't add themselves to a team they don't own")

        # User can't add a contributor to a team they don't own
        response = c1.post(reverse('collaborate_team_update_view', kwargs={'pk': str(self.team_2.id)}),
                           {'contributors': str(self.user_2.id)})
        self.assertEqual(response.status_code, 403, "User can't add a contributor to a team they don't own")

        # User can't add themselves to a team they don't own
        response = c1.post(reverse('collaborate_team_add_remove_contributor', kwargs={'pk': str(self.team_2.id)}),
                           {'add_contributor': True, 'contributor_id': str(self.user_1.contributor_id)})
        self.assertEqual(response.status_code, 403)
        self.team_2.refresh_from_db()
        self.assertFalse(self.user_1 in self.team_2.contributors.all(), "User can't add themselves to a team they don't own")

        # User can't add a contributor to a team they don't own
        response = c1.post(reverse('collaborate_team_add_remove_contributor', kwargs={'pk': str(self.team_2.id)}),
                           {'add_contributor': True, 'contributor_id': str(self.user_2.contributor_id)})
        self.assertEqual(response.status_code, 403)
        self.team_2.refresh_from_db()
        self.assertFalse(self.user_2 in self.team_2.contributors.all(), "User can't add a contributor to a team they don't own")

        # User can't add themselves as contributor to their team
        response = c1.post(reverse('collaborate_team_add_remove_contributor', kwargs={'pk': str(self.team_1.id)}),
                           {'add_contributor': True, 'contributor_id': str(self.user_1.contributor_id)})
        self.assertEqual(response.status_code, 302)
        self.team_1.refresh_from_db()
        self.assertFalse(self.user_1 in self.team_1.contributors.all(), "User can't add themselves as contributor to their team")

        # User can add a contributor to their team
        response = c1.post(reverse('collaborate_team_add_remove_contributor', kwargs={'pk': str(self.team_1.id)}),
                           {'add_contributor': True, 'contributor_id': str(self.user_2.contributor_id)})
        self.assertEqual(response.status_code, 302)
        self.team_1.refresh_from_db()
        self.assertTrue(self.user_2 in self.team_1.contributors.all(), "User can add a contributor to their team")

    def test_team_deletion(self):
        c1 = Client()
        login1 = c1.login(username=self.user_1.username, password=self.password)
        self.assertTrue(login1, "User can login")

        # User can't delete a team they don't own
        response = c1.get(reverse('collaborate_team_delete_view', kwargs={'pk': str(self.team_2.id)}))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ColanderTeam.objects.filter(id=str(self.team_2.id)).exists())
