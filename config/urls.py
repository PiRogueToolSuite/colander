from allauth_2fa.views import TwoFactorSetup, TwoFactorAuthenticate, TwoFactorBackupTokens, TwoFactorRemove
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from colander.core.views.actor_views import ActorDetailsView, ActorUpdateView, ActorCreateView, delete_actor_view
from colander.core.views.artifact_views import ArtifactDetailsView, ArtifactCreateView, ArtifactUpdateView, download_artifact, \
    download_artifact_signature
from colander.core.views.comment_views import create_comment_view, delete_comment_view, CommentUpdateView
from colander.core.views.device_views import DeviceDetailsView, DeviceCreateView, DeviceUpdateView, delete_device_view
from colander.core.views.documentation_views import write_documentation_view
from colander.core.views.enrich_view import enrich_observable
from colander.core.views.experiment_views import PiRogueExperimentCreateView, PiRogueExperimentUpdateView, \
    PiRogueExperimentDetailsView, start_decryption, delete_experiment_view
from colander.core.views.investigate_views import investigate_search_view
from colander.core.views.obversable_views import ObservableCreateView, ObservableRelationCreateView, \
    ObservableUpdateView, \
    ObservableRelationUpdateView, ObservableDetailsView, ObservableRelationDetailsView, delete_observable_view
from colander.core.views.proxys import cyber_chef_view
from colander.core.views.relation_views import create_or_edit_entity_relation_view, delete_relation_view
from colander.core.views.views import collect_base_view, \
    report_base_view, collect_cases_select_view, CaseCreateView, \
    CaseUpdateView, entity_exists, quick_search, CaseDetailsView, download_case_public_key, \
    save_case_documentation_view, enable_documentation_editor, disable_documentation_editor, quick_creation_view
from colander.core.views.event_views import EventCreateView, EventUpdateView, EventDetailsView, delete_event_view
from colander.core.views.threat_views import ThreatCreateView, ThreatUpdateView, ThreatDetailsView, delete_threat_view
from colander.users.views import UserTwoFactorSetup
urlpatterns = [
      path(r'jsi18n/', JavaScriptCatalog.as_view(), name='jsi18n'),
      path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
      # path("about/", TemplateView.as_view(template_name="index.html"), name="about"),
      path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
      # Django Admin, use {% url 'admin:index' %}
      path(settings.ADMIN_URL, admin.site.urls),
      # User management
      path("users/", include("colander.users.urls", namespace="users")),
      path('accounts/2fa/setup', UserTwoFactorSetup.as_view(), name="two-factor-setup",),
      path('accounts/2fa/authenticate', TwoFactorAuthenticate.as_view(), name="two-factor-authenticate",),
      path('accounts/2fa/backup-tokens', TwoFactorBackupTokens.as_view(), name="two-factor-backup-tokens",),
      path('accounts/2fa/remove', TwoFactorRemove.as_view(), name="two-factor-remove",),

      path("accounts/", include("allauth.urls")),

      path('martor/', include('martor.urls')),

      # path("evidences", evidences_view),
      # path('dj-rest-auth/', include('dj_rest_auth.urls')),
      # path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
      # Your stuff: custom urls includes go here

      path("quick_search/", quick_search, name='quick_search_view'),

      path("collect/", collect_base_view, name="collect_base_view"),
      path("collect/quick", quick_creation_view, name="collect_quick_creation_view"),
      path("collect/actor", ActorCreateView.as_view(), name="collect_actor_create_view"),
      path("collect/actor/<slug:pk>", ActorUpdateView.as_view(), name="collect_actor_update_view"),
      path("collect/actor/<slug:pk>/details", ActorDetailsView.as_view(), name="collect_actor_details_view"),
      path("collect/actor/<slug:pk>/delete", delete_actor_view, name="collect_actor_delete_view"),

      path("collect/case", CaseCreateView.as_view(), name="collect_case_create_view"),
      path("document/case", write_documentation_view, name="document_case_write_doc_view"),
      path("collect/case/<slug:pk>", CaseUpdateView.as_view(), name="collect_case_update_view"),
      path("collect/case/<slug:pk>/details", CaseDetailsView.as_view(), name="collect_case_details_view"),
      path("collect/case/<slug:pk>/select", collect_cases_select_view, name="collect_cases_select_view"),
      path("collect/case/<slug:pk>/doc/save", save_case_documentation_view, name="collect_cases_save_doc_view"),
      path("collect/case/<slug:pk>/download_key", download_case_public_key, name="collect_cases_download_key_view"),

      path("collect/artifact", ArtifactCreateView.as_view(), name="collect_artifact_create_view"),
      path("collect/artifact/<slug:pk>", ArtifactUpdateView.as_view(), name="collect_artifact_update_view"),
      path("collect/artifact/<slug:pk>/details", ArtifactDetailsView.as_view(), name="collect_artifact_details_view"),
      path("collect/artifact/<slug:pk>/download", download_artifact, name="collect_artifact_download_view"),
      path("collect/artifact/<slug:pk>/download_sig", download_artifact_signature, name="collect_artifact_download_signature_view"),

      path("collect/device", DeviceCreateView.as_view(), name="collect_device_create_view"),
      path("collect/device/<slug:pk>", DeviceUpdateView.as_view(), name="collect_device_update_view"),
      path("collect/device/<slug:pk>/details", DeviceDetailsView.as_view(), name="collect_device_details_view"),
      path("collect/device/<slug:pk>/delete", delete_device_view, name="collect_device_delete_view"),

      path("collect/event", EventCreateView.as_view(), name="collect_event_create_view"),
      path("collect/event/<slug:pk>", EventUpdateView.as_view(), name="collect_event_update_view"),
      path("collect/event/<slug:pk>/details", EventDetailsView.as_view(), name="collect_event_details_view"),
      path("collect/event/<slug:pk>/delete", delete_event_view, name="collect_event_delete_view"),

      path("collect/observable", ObservableCreateView.as_view(), name="collect_observable_create_view"),
      path("collect/observable/<slug:pk>", ObservableUpdateView.as_view(), name="collect_observable_update_view"),
      path("collect/observable/<slug:pk>/details", ObservableDetailsView.as_view(), name="collect_observable_details_view"),
      path("collect/observable/<slug:pk>/delete", delete_observable_view, name="collect_observable_delete_view"),

      path("collect/entity_relation", create_or_edit_entity_relation_view, name="collect_entity_relation_create_view"),
      path("collect/entity_relation/<slug:pk>/delete", delete_relation_view, name="collect_entity_relation_delete_view"),

      # path("collect/relation", ObservableRelationCreateView.as_view(), name="collect_relation_create_view"),
      # path("collect/relation/<slug:pk>", ObservableRelationUpdateView.as_view(), name="collect_relation_update_view"),


      path("collect/threat", ThreatCreateView.as_view(), name="collect_threat_create_view"),
      path("collect/threat/<slug:pk>", ThreatUpdateView.as_view(), name="collect_threat_update_view"),
      path("collect/threat/<slug:pk>/details", ThreatDetailsView.as_view(), name="collect_threat_details_view"),
      path("collect/threat/<slug:pk>/delete", delete_threat_view, name="collect_threat_delete_view"),

      path("collect/experiment", PiRogueExperimentCreateView.as_view(), name="collect_experiment_create_view"),
      path("collect/experiment/<slug:pk>", PiRogueExperimentUpdateView.as_view(), name="collect_experiment_update_view"),
      path("collect/experiment/<slug:pk>/details", PiRogueExperimentDetailsView.as_view(), name="collect_experiment_details_view"),
      path("collect/experiment/<slug:pk>/delete", delete_experiment_view, name="collect_experiment_delete_view"),
      path("collect/experiment/<slug:pk>/decrypt", start_decryption, name="collect_experiment_decryption_view"),

      path("analyze/<slug:observable_id>", enrich_observable, name="analyze_base_view"),

      path("entity/<str:type>/<str:value>", entity_exists, name="entity_exists_view"),

      path("investigate/", investigate_search_view, name="investigate_base_view"),
      path("report/", report_base_view, name="report_base_view"),

      path("document/enable", enable_documentation_editor, name="enable_documentation_editor_view"),
      path("document/disable", disable_documentation_editor, name="disable_documentation_editor_view"),

      path("comment/", create_comment_view, name="create_comment_view"),
      path("comment/<slug:pk>/edit", CommentUpdateView.as_view(), name="update_comment_view"),
      path("comment/<slug:pk>/delete", delete_comment_view, name="delete_comment_view"),

      path("cyberchef", cyber_chef_view, name="cyberchef_view"),
      # path("cyberchef_input/<path:path>", cyber_chef_input_view, name="cyberchef_view_input"),
      path("cyberchef/<path:path>", cyber_chef_view, name="cyberchef_view_with_path")

    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router")),
    # DRF auth token
    # path("api/auth-token/", obtain_auth_token),
    # path("api/artifacts/<slug:pk>", ApiArtifactDetails.as_view(), name='api_list_artifacts'),
    # path("api/artifacts/<slug:pk>/download", ApiArtifactDownload.as_view(), name='api_download_artifact'),
    # API Schema
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
