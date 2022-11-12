from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from colander.core.obversable_views import ObservableCreateView, ObservableRelationCreateView, ObservableUpdateView, \
    ObservableRelationUpdateView
from colander.core.views import collect_base_view, analyze_base_view, investigate_base_view, \
    report_base_view, ArtifactCreateView, ArtifactUpdateView, collect_cases_select_view, CaseCreateView, \
    CaseUpdateView, ActorUpdateView, ActorCreateView, DeviceCreateView, DeviceUpdateView, EventCreateView, \
    EventUpdateView

urlpatterns = [
                  path(r'jsi18n/', JavaScriptCatalog.as_view(), name='jsi18n'),
                  path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
                  path(
                      "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
                  ),
                  # Django Admin, use {% url 'admin:index' %}
                  path(settings.ADMIN_URL, admin.site.urls),
                  # User management
                  path("users/", include("colander.users.urls", namespace="users")),
                  path("accounts/", include("allauth.urls")),

                  # path("evidences", evidences_view),
                  # path('dj-rest-auth/', include('dj_rest_auth.urls')),
                  # path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
                  # Your stuff: custom urls includes go here

                  path("collect/", collect_base_view, name="collect_base_view"),
                  path("collect/actor", ActorCreateView.as_view(), name="collect_actor_create_view"),
                  path("collect/actor/<slug:pk>", ActorUpdateView.as_view(), name="collect_actor_update_view"),
                  path("collect/case", CaseCreateView.as_view(), name="collect_case_create_view"),
                  path("collect/case/<slug:pk>", CaseUpdateView.as_view(), name="collect_case_update_view"),
                  path("collect/case/<slug:pk>/select", collect_cases_select_view, name="collect_cases_select_view"),
                  path("collect/artifact", ArtifactCreateView.as_view(), name="collect_artifact_create_view"),
                  path("collect/artifact/<slug:pk>", ArtifactUpdateView.as_view(), name="collect_artifact_update_view"),
                  path("collect/device", DeviceCreateView.as_view(), name="collect_device_create_view"),
                  path("collect/device/<slug:pk>", DeviceUpdateView.as_view(), name="collect_device_update_view"),
                  path("collect/event", EventCreateView.as_view(), name="collect_event_create_view"),
                  path("collect/event/<slug:pk>", EventUpdateView.as_view(), name="collect_event_update_view"),
                  path("collect/observable", ObservableCreateView.as_view(), name="collect_observable_create_view"),
                  path("collect/observable/<slug:pk>", ObservableUpdateView.as_view(),
                       name="collect_observable_update_view"),
                  path("collect/relation", ObservableRelationCreateView.as_view(), name="collect_relation_create_view"),
                  path("collect/relation/<slug:pk>", ObservableRelationUpdateView.as_view(),
                       name="collect_relation_update_view"),
                  path("analyze/", analyze_base_view, name="analyze_base_view"),
                  path("investigate/", investigate_base_view, name="investigate_base_view"),
                  path("report/", report_base_view, name="report_base_view"),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router")),
    # path('api/auth/facebook/connect/', FacebookConnect.as_view(), name='fb_connect'),
    # path('api/auth/twitter/connect/', TwitterConnect.as_view(), name='twitter_connect'),
    # path('api/auth/github/connect/', csrf_exempt(GithubConnect.as_view()), name='github_connect'),
    # path('api/auth/github/url/', github_views.oauth2_login, name='github_url'),
    # path('api/auth/github/callback/', github_callback, name='github_callback'),
    # DRF auth token
    # path("api/auth-token/", obtain_auth_token),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
