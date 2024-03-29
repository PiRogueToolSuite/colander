from urllib.parse import quote, urlencode

from allauth_2fa.views import TwoFactorSetup
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView

User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):

    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self):
        assert (
            self.request.user.is_authenticated
        )  # for mypy to know that the user is authenticated
        return self.request.user.get_absolute_url()

    def get_object(self):
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):

    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()


class UserTwoFactorSetup(TwoFactorSetup):
    def generate_totp_url(self, secret):
        params = {
            "secret": secret,
            "algorithm": "SHA1",
            "digits": self.device.digits,
            "period": self.device.step,
            "issuer": self.get_qr_code_kwargs().get('issuer', ''),
        }
        return f"otpauth://totp/{quote(self.get_qr_code_kwargs().get('label', ''))}?{urlencode(params)}"


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["totp_url"] = self.generate_totp_url(context.get('secret'))
        return context
