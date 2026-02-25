from rest_framework.authentication import TokenAuthentication, BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

from colander.core.models import DeviceMonitoring


class BearerTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'
    """Some external requesters use 'Authorization: Bearer' preamble
    to authenticate and not the 'non standard' 'Token' one used by DRF.
    """


def get_webhook_token(keyword, header):
    if not header or not header.startswith(f'{keyword} '):
        return None

    try:
        token = header.strip().split(' ')[1]
    except (Exception,):
        return None
    return token


def get_webhook_object_from_auth_header(request, model_class):
    if not hasattr(model_class, 'authentication_token'):
        return None

    keyword = 'Secret'
    header = request.META.get('HTTP_X_COLANDER_WEBHOOK')
    token = get_webhook_token(keyword, header)

    try:
        obj = model_class.objects.get(authentication_token=token)
    except model_class.DoesNotExist:
        return None
    return obj


class CanSendToWebhook(BasePermission):
    def __init__(self, model_class):
        self.model_class = model_class
        super().__init__()

    def has_permission(self, request, view):
        return get_webhook_object_from_auth_header(request, self.model_class) is not None


class DeviceMonitoringWebhookAuthentication(BaseAuthentication):
    def authenticate(self, request):
        obj = get_webhook_object_from_auth_header(request, DeviceMonitoring)
        if not obj or not hasattr(obj, 'owner'):
            raise AuthenticationFailed()
        return obj.owner, None
