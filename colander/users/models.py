from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token


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

    @property
    def token(self):
        return self.get_auth_token()

    def get_auth_token(self, reset=False):
        print('Allllllo !')
        if reset:
            Token.objects.filter(user=self).delete()
        token, _ = Token.objects.get_or_create(user=self)
        print(token)
        return token

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})
