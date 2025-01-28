from django.urls import path

from colander.users.views import (
    user_detail_view,
    user_redirect_view,
    user_update_view,
    regenerate_token_api,
)

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
    path("<str:username>/regenerate-token", view=regenerate_token_api, name="regenerate_token"),
]
