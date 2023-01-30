from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from colander.core.es_utils import create_geoip_pipeline


class CoreConfig(AppConfig):
    name = "colander.core"
    verbose_name = _("Core")

    def ready(self):
        print('Ready')
        create_geoip_pipeline()
        try:
            import colander.users.signals  # noqa F401
        except ImportError:
            pass
