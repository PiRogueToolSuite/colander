from django.contrib.auth.signals import user_login_failed
from django.utils import timezone
from ipware import get_client_ip
import logging

logger = logging.getLogger(__name__)

def build_auth_log_string(message: str, username: str, email: str, request):
    client_ip, is_routable = "", False
    if request:
        client_ip, is_routable = get_client_ip(request)
    msg = "{message} username:[{username}] email:[{email}] ip:[{ip}] datetime:[{now}] routable:[{is_routable}]".format(
        message=message,
        username=username or "",
        email=email or "",
        ip=client_ip,
        is_routable=is_routable,
        now=timezone.now(),
    )
    return msg


def handle_user_login_failed(sender, credentials, request=None, **kwargs):
    username = credentials.get("username", None)
    email = credentials.get("email", None)
    log_string = build_auth_log_string("COLANDER_AUTH_FAILURE", username, email, request)
    logger.error(log_string)


user_login_failed.connect(handle_user_login_failed)
