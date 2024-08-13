import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField, Q
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token

from colander.core.models import Case, ColanderTeam


class User(AbstractUser):
    """
    Default custom user model for colander.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    DEVICE = 'DEVICE'
    USER = 'USER'
    APP = 'APP'
    USER_TYPE = [
        (USER, _('Regular user')),
        (APP, _('External application')),
        (DEVICE, _('External device')),
    ]
    #: First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    type = CharField(
        max_length=16,
        choices=USER_TYPE,
        default=USER,
    )
    contributor_id = models.UUIDField(
        default=uuid.uuid4,
        help_text=_('Contributor ID.'),
        editable=False
    )

    @property
    def token(self):
        return self.get_auth_token()

    @cached_property
    def all_my_teams(self):
        return self.get_my_teams()

    @cached_property
    def my_teams(self):
        return self.teams_as_owner.all()

    @cached_property
    def my_teams_as_collaborator(self):
        return self.teams_as_contrib.all()

    @cached_property
    def my_cases(self):
        return Case.objects.filter(owner=self)

    @cached_property
    def all_my_cases(self):
        teams = self.all_my_teams
        return Case.objects.filter(Q(teams__in=teams) | Q(owner=self)).distinct().all()

    def get_my_teams(self):
        teams = []
        teams.extend(self.teams_as_owner.all())
        teams.extend(self.teams_as_contrib.all())
        return list(set(teams))

    @cached_property
    def my_teams_as_qset(self):
        return ColanderTeam.objects.filter(Q(owner=self) | Q(contributors=self)).distinct().all()

    def get_auth_token(self, reset=False):
        if reset:
            Token.objects.filter(user=self).delete()
        token, _ = Token.objects.get_or_create(user=self)
        return token

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})
