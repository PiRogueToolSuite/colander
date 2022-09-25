from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "colander.core"
    verbose_name = _("Core")

    def ready(self):
        try:
            import colander.users.signals  # noqa F401
        except ImportError:
            pass
