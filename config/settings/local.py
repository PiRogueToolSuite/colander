from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="udM2kuRooejDnEbyBb21h8BSEChsELAZWn4NI2dP4uajjHXIRYQfRztiq2GEFAQS",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "*", "127.0.0.1"]

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS  # noqa F405


# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
if env("USE_DOCKER") == "yes":
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]  # noqa F405

TEMPLATES[0]['OPTIONS']['debug'] = True

# Your stuff...
# ------------------------------------------------------------------------------
# SOCIALACCOUNT_PROVIDERS = {
#     "openid_connect": {
#         "SERVERS": [
#             {
#                 "id": "keycloak",  # 30 characters or less
#                 "name": "Colander authentication",
#                 "server_url": "http://192.168.0.12:8003/realms/Colander",
#                 # Optional token endpoint authentication method.
#                 # May be one of "client_secret_basic", "client_secret_post"
#                 # If omitted, a method from the the server's
#                 # token auth methods list is used
#                 "token_auth_method": "client_secret_basic",
#                 "APP": {
#                     "client_id": "colander",
#                     "secret": "aJnfi6xIsvaxm6SEDehKoP7GBt4FADyj",
#                 },
#             },
#         ]
#     }
# }

CYBERCHEF_FQDN = env('CYBERCHEF_FQDN', default='beta.cyberchef.defensive-lab.agency')
THREATR_FQDN = env('THREATR_FQDN', default='10.8.0.14:9000')
CYBERCHEF_BASE_URL = env('CYBERCHEF_BASE_URL', default=f'https://{CYBERCHEF_FQDN}')
THREATR_BASE_URL = env('THREATR_BASE_URL', default=f'http://{THREATR_FQDN}')
