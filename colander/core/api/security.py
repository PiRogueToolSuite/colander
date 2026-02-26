from typing import Optional

from rest_framework.authentication import TokenAuthentication, BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

from colander.core.models import ApiToken


class BearerTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'
    """Some external requesters use 'Authorization: Bearer' preamble
    to authenticate and not the 'non standard' 'Token' one used by DRF.
    """


class ApiTokenAuthentication(BaseAuthentication):
    keyword = 'Secret'
    header_name = 'HTTP_X_AUTHENTICATION'  # X-Authentication

    @classmethod
    def get_token_value_from_header(cls, request):
        header = request.META.get(cls.header_name)
        if not header or not header.startswith(f'{cls.keyword} '):
            return None
        try:
            token = header.strip().split(' ')[1]
        except (Exception,):
            return None
        return token

    @classmethod
    def get_token(cls, request) -> Optional[ApiToken]:
        token = cls.get_token_value_from_header(request)
        try:
            api_token = ApiToken.objects.get(token=token)
        except ApiToken.DoesNotExist:
            return None
        return api_token

    def authenticate(self, request):
        token = self.get_token(request)
        if not token:
            raise AuthenticationFailed()
        return token.owner, token


class HasViewPermission(BasePermission):
    def has_permission(self, request, view):
        view_name = f'{view.basename}.{view.action}'
        api_token = ApiTokenAuthentication.get_token(request)
        if not api_token:
            return False
        if view_name not in api_token.views:
            return False
        request.api_token = api_token
        return True
