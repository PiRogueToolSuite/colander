from django.test import TestCase, Client
from django.urls import reverse

from colander.core.models import Case, ColanderTeam, ActorType, Actor
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

    def test_collect_actors(self):
        c1 = Client()
        login1 = c1.login(username=self.user_1.username, password=self.password)
        c2 = Client()
        login2 = c2.login(username=self.user_2.username, password=self.password)
        actor_type = ActorType.objects.create(short_name='APT', name='apt')

        # User can't add an actor to a case they can't contribute to
        response = c1.post(reverse('collect_actor_create_view',
                                   kwargs={'case_id': str(self.case_2.id)}),
                           {
                               'name': 'foo',
                               'type': str(actor_type.id)
                           })
        self.assertEqual(response.status_code, 403, "User can't add an actor to a case they can't contribute to")

        # User can add an actor to a case they own
        response = c1.post(reverse('collect_actor_create_view',
                                   kwargs={'case_id': str(self.case_1.id)}),
                           {
                               'name': 'foo',
                               'type': str(actor_type.id),
                               'tlp': 'WHITE',
                               'pap': 'WHITE',
                               'save_actor': '',
                           })
        # print(response.content)
        self.assertEqual(response.status_code, 302, "User can add an actor to a case they own")
        actor_1 = Actor.objects.get(name='foo')
        self.assertIsNotNone(actor_1)

        # User can't edit an actor to a case they can't contribute to
        response = c2.post(reverse('collect_actor_update_view',
                                   kwargs={'case_id': str(self.case_1.id), 'pk': str(actor_1.id)}),
                           {
                               'name': 'bar',
                               'type': str(actor_type.id)
                           })
        self.assertEqual(response.status_code, 403, "User can't edit an actor to a case they can't contribute to")
        actor_1.refresh_from_db()
        self.assertEqual(actor_1.name, 'foo', "User can't edit an actor to a case they can't contribute to")

        # User can't delete an actor to a case they can't contribute to
        response = c2.get(reverse('collect_actor_delete_view',
                                   kwargs={'case_id': str(self.case_1.id), 'pk': str(actor_1.id)}))
        self.assertEqual(response.status_code, 403, "User can't delete an actor to a case they can't contribute to")
        actor_1.refresh_from_db()
        self.assertEqual(actor_1.name, 'foo', "User can't delete an actor to a case they can't contribute to")

