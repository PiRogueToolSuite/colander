from typing import Any

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth_2fa.adapter import OTPAdapter
from django.conf import settings
from django.http import HttpRequest


class AccountAdapter(OTPAdapter):
    def is_open_for_signup(self, request: HttpRequest):
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)
