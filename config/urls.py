from allauth_2fa.views import TwoFactorAuthenticate, TwoFactorBackupTokens, TwoFactorRemove
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog
from rest_framework.schemas import get_schema_view

from colander.core.graph.views import case_graph, case_subgraph
from colander.core.views import import_views
from colander.core.views.actor_views import ActorCreateView, ActorDetailsView, ActorUpdateView, delete_actor_view
from colander.core.views.artifact_views import (
    ArtifactCreateView,
    ArtifactDetailsView,
    ArtifactUpdateView,
    delete_artifact_view,
    download_artifact,
    download_artifact_signature,
    view_artifact,
)
from colander.core.views.collaborate_views import (
    ColanderTeamCreateView,
    ColanderTeamDetailsView,
    ColanderTeamUpdateView,
    add_remove_team_contributor,
    delete_team_view,
)
from colander.core.views.comment_views import CommentUpdateView, create_comment_view, delete_comment_view
from colander.core.views.data_fragment_views import (
    DataFragmentCreateView,
    DataFragmentDetailsView,
    DataFragmentUpdateView,
    delete_data_fragment_view,
)
from colander.core.views.detection_rule_views import (
    DetectionRuleCreateView,
    DetectionRuleDetailsView,
    DetectionRuleUpdateView,
    delete_detection_rule_view,
)
from colander.core.views.device_views import DeviceCreateView, DeviceDetailsView, DeviceUpdateView, delete_device_view
from colander.core.views.documentation_views import write_documentation_view
from colander.core.views.dropped_files_views import triage_view
from colander.core.views.event_views import EventCreateView, EventDetailsView, EventUpdateView, delete_event_view
from colander.core.views.experiment_views import (
    PiRogueExperimentAnalysisReportView,
    PiRogueExperimentCreateView,
    PiRogueExperimentDetailsView,
    PiRogueExperimentUpdateView,
    delete_experiment_view,
    save_decoded_content_view,
    start_decryption,
    start_detection,
)
from colander.core.views.graph_views import graph_base_view
from colander.core.views.import_views import import_view, import_misp_view
from colander.core.views.investigate_views import investigate_search_view
from colander.core.views.obversable_views import (
    ObservableCreateView,
    ObservableDetailsView,
    ObservableUpdateView,
    capture_observable_view,
    delete_observable_view,
)
from colander.core.views.outgoing_feeds_views import (
    DetectionRuleExportFeedCreateView,
    DetectionRuleExportFeedUpdateView,
    EntityExportFeedCreateView,
    EntityExportFeedUpdateView,
    delete_detection_rule_export_feed_view,
    delete_entity_export_feed_view,
    detection_rule_export_feed_view,
    entity_export_feed_view,
)
from colander.core.views.relation_views import create_or_edit_entity_relation_view, delete_relation_view
from colander.core.views.status_views import colander_status_view
from colander.core.views.subgraphs_views import SubGraphCreateView, delete_subgraph_view, \
    SubGraphUpdateView, subgraph_editor_view, subgraph_thumbnail_view, subgraph_pin_toggle_view
from colander.core.views.threat_views import ThreatCreateView, ThreatDetailsView, ThreatUpdateView, delete_threat_view
from colander.core.views.upload_views import append_to_upload, initialize_upload
from colander.core.views.views import (
    CaseCreateView,
    CaseDetailsView,
    CaseUpdateView,
    case_close,
    case_workspace_view,
    cases_select_view,
    collaborate_base_view,
    cron_ish_view,
    download_case_public_key,
    export_case_documentation_as_markdown_view,
    feeds_view,
    landing_view,
    quick_creation_view,
    quick_search,
    save_case_documentation_view,
    vues_view, entity_thumbnail_view,
)
from colander.users.views import UserTwoFactorSetup

case_contextualized_url_patterns = [
    path("", case_workspace_view, name="case_workspace_view"),
    path("collect", quick_creation_view, name="collect_quick_creation_view"),
    path("collect/actor", ActorCreateView.as_view(), name="collect_actor_create_view"),
    path("collect/actor/<slug:pk>", ActorDetailsView.as_view(), name="collect_actor_details_view"),
    path("collect/actor/<slug:pk>/edit", ActorUpdateView.as_view(), name="collect_actor_update_view"),
    path("collect/actor/<slug:pk>/delete", delete_actor_view, name="collect_actor_delete_view"),

    path("collect/artifact", ArtifactCreateView.as_view(), name="collect_artifact_create_view"),
    path("collect/artifact/upload", initialize_upload, name="initialize_upload"),
    path("collect/artifact/upload/<str:upload_id>", append_to_upload, name="append_to_upload"),
    path("collect/artifact/<slug:pk>", ArtifactDetailsView.as_view(), name="collect_artifact_details_view"),
    path("collect/artifact/<slug:pk>/edit", ArtifactUpdateView.as_view(), name="collect_artifact_update_view"),
    path("collect/artifact/<slug:pk>/delete", delete_artifact_view, name="collect_artifact_delete_view"),
    path("collect/artifact/<slug:pk>/view", view_artifact, name="collect_artifact_view_view"),
    path("collect/artifact/<slug:pk>/download", download_artifact, name="collect_artifact_download_view"),
    path("collect/artifact/<slug:pk>/download_sig", download_artifact_signature, name="collect_artifact_download_signature_view"),

    path("collect/device", DeviceCreateView.as_view(), name="collect_device_create_view"),
    path("collect/device/<slug:pk>", DeviceDetailsView.as_view(), name="collect_device_details_view"),
    path("collect/device/<slug:pk>/edit",DeviceUpdateView.as_view(), name="collect_device_update_view"),
    path("collect/device/<slug:pk>/delete", delete_device_view, name="collect_device_delete_view"),

    path("collect/detection_rule", DetectionRuleCreateView.as_view(), name="collect_detection_rule_create_view"),
    path("collect/detection_rule/<slug:pk>", DetectionRuleDetailsView.as_view(), name="collect_detection_rule_details_view"),
    path("collect/detection_rule/<slug:pk>/edit", DetectionRuleUpdateView.as_view(), name="collect_detection_rule_update_view"),
    path("collect/detection_rule/<slug:pk>/delete", delete_detection_rule_view, name="collect_detection_rule_delete_view"),

    path("collect/threat", ThreatCreateView.as_view(), name="collect_threat_create_view"),
    path("collect/threat/<slug:pk>", ThreatDetailsView.as_view(), name="collect_threat_details_view"),
    path("collect/threat/<slug:pk>/edit", ThreatUpdateView.as_view(), name="collect_threat_update_view"),
    path("collect/threat/<slug:pk>/delete", delete_threat_view, name="collect_threat_delete_view"),

    path("collect/observable", ObservableCreateView.as_view(), name="collect_observable_create_view"),
    path("collect/observable/<slug:pk>", ObservableDetailsView.as_view(), name="collect_observable_details_view"),
    path("collect/observable/<slug:pk>/capture", capture_observable_view, name="collect_observable_capture_view"),
    path("collect/observable/<slug:pk>/edit", ObservableUpdateView.as_view(), name="collect_observable_update_view"),
    path("collect/observable/<slug:pk>/delete", delete_observable_view, name="collect_observable_delete_view"),

    path("collect/event", EventCreateView.as_view(), name="collect_event_create_view"),
    path("collect/event/<slug:pk>", EventDetailsView.as_view(), name="collect_event_details_view"),
    path("collect/event/<slug:pk>/edit", EventUpdateView.as_view(), name="collect_event_update_view"),
    path("collect/event/<slug:pk>/delete", delete_event_view, name="collect_event_delete_view"),

    path("collect/data_fragment", DataFragmentCreateView.as_view(), name="collect_data_fragment_create_view"),
    path("collect/data_fragment/<slug:pk>", DataFragmentDetailsView.as_view(), name="collect_data_fragment_details_view"),
    path("collect/data_fragment/<slug:pk>/edit", DataFragmentUpdateView.as_view(), name="collect_data_fragment_update_view"),
    path("collect/data_fragment/<slug:pk>/delete", delete_data_fragment_view, name="collect_data_fragment_delete_view"),

    path("collect/entity_relation", create_or_edit_entity_relation_view, name="collect_entity_relation_create_view"),
    path("collect/entity_relation/<slug:pk>/delete", delete_relation_view, name="collect_entity_relation_delete_view"),

    path("collect/experiment", PiRogueExperimentCreateView.as_view(), name="collect_experiment_create_view"),
    path("collect/experiment/<slug:pk>/edit", PiRogueExperimentUpdateView.as_view(), name="collect_experiment_update_view"),
    path("collect/experiment/<slug:pk>", PiRogueExperimentDetailsView.as_view(), name="collect_experiment_details_view"),
    path("collect/experiment/<slug:pk>/delete", delete_experiment_view, name="collect_experiment_delete_view"),
    path("collect/experiment/<slug:pk>/decrypt", start_decryption, name="collect_experiment_decryption_view"),
    path("collect/experiment/<slug:pk>/detect", start_detection, name="collect_experiment_detection_view"),
    path("collect/experiment/<slug:pk>/analysis_report", PiRogueExperimentAnalysisReportView.as_view(), name="collect_experiment_analysis_report_view"),
    path("collect/experiment/<slug:pk>/save_decoded", save_decoded_content_view, name="collect_experiment_save_decoded_content_view"),

    path("graph", graph_base_view, name="graph_base_view"),
    path("graph/subgraphs", SubGraphCreateView.as_view(), name="subgraph_create_view"),
    path("graph/<slug:pk>", subgraph_editor_view, name="subgraph_editor_view"),
    path("graph/<slug:pk>/datasource", case_subgraph, name="case_subgraph"),
    path("graph/<slug:pk>/edit", SubGraphUpdateView.as_view(), name="subgraph_update_view"),
    path("graph/<slug:pk>/delete", delete_subgraph_view, name="subgraph_delete_view"),
    path("graph/<slug:pk>/thumbnail.png", subgraph_thumbnail_view, name="subgraph_thumbnail_view"),
    path("graph/<slug:pk>/toggle-pin", subgraph_pin_toggle_view, name="subgraph_pin_toggle_view"),

    path("entity/<slug:pk>/thumbnail.png", entity_thumbnail_view, name="entity_thumbnail_view"),

    path("document", write_documentation_view, name="document_case_write_doc_view"),
    path("document/save", save_case_documentation_view, name="cases_save_doc_view"),
    path("document/export/markdown", export_case_documentation_as_markdown_view, name="cases_doc_export_as_markdown_view"),

    path("feeds", feeds_view, name="feeds_view"),

    path("feeds/detection_rules", DetectionRuleExportFeedCreateView.as_view(), name="feeds_detection_rule_out_feed_create_view"),
    path("feeds/detection_rules/<slug:pk>/edit", DetectionRuleExportFeedUpdateView.as_view(), name="feeds_detection_rule_out_feed_update_view"),
    path("feeds/detection_rules/<slug:pk>/delete", delete_detection_rule_export_feed_view, name="feeds_detection_rule_out_feed_delete_view"),

    path("feeds/entity_out_feed", EntityExportFeedCreateView.as_view(), name="feeds_entity_out_feed_create_view"),
    path("feeds/entity_out_feed/<slug:pk>/edit", EntityExportFeedUpdateView.as_view(), name="feeds_entity_out_feed_update_view"),
    path("feeds/entity_out_feed/<slug:pk>/delete", delete_entity_export_feed_view, name="feeds_entity_out_feed_delete_view"),

    path("investigate/", investigate_search_view, name="investigate_base_view"),

    path("import", import_view, name="import_view"),
    path("import/misp", import_misp_view, name="import_misp_view"),
    path("import/csv", TemplateView.as_view(template_name="import/csv.html"), name="import_csv_view"),
]

urlpatterns = [
      path(r'jsi18n/', JavaScriptCatalog.as_view(), name='jsi18n'),
      path("", landing_view, name="home"),
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

      path("quick_search/", quick_search, name='quick_search_view'),

      path("status/", colander_status_view, name='colander_status_view'),

      path("collaborate/", collaborate_base_view, name="collaborate_base_view"),
      path("collaborate/team", ColanderTeamCreateView.as_view(), name="collaborate_team_create_view"),
      path("collaborate/team/<slug:pk>", ColanderTeamDetailsView.as_view(), name="collaborate_team_details_view"),
      path("collaborate/team/<slug:pk>/edit", ColanderTeamUpdateView.as_view(), name="collaborate_team_update_view"),
      path("collaborate/team/<slug:pk>/contribs", add_remove_team_contributor, name="collaborate_team_add_remove_contributor"),
      path("collaborate/team/<slug:pk>/delete", delete_team_view, name="collaborate_team_delete_view"),
      path("feed/detection_rules/colander_<slug:pk>.rules", detection_rule_export_feed_view, name="collaborate_detection_rule_out_feed_view-rules"),  # to please suricata-update 🤪🤦‍♀️
      path("feed/detection_rules/<slug:pk>", detection_rule_export_feed_view, name="collaborate_detection_rule_out_feed_view"),
      path("feed/entities/<slug:pk>", entity_export_feed_view, name="collaborate_entity_out_feed_view"),
      path("case", CaseCreateView.as_view(), name="case_base_view"),
      path("case/create", CaseCreateView.as_view(), name="case_create_view"),
      path("case/close", case_close, name="case_close"),
      path("case/<slug:pk>/edit", CaseUpdateView.as_view(), name="case_update_view"),
      path("case/<slug:pk>", CaseDetailsView.as_view(), name="case_details_view"),
      path("case/<slug:pk>/graph", case_graph, name="case_graph"),
      path("case/<slug:pk>/select", cases_select_view, name="cases_select_view"),
      path("case/<slug:pk>/download_key", download_case_public_key, name="cases_download_key_view"),
      path("drops/", triage_view, name="dropped_files_triage_base_view"),
      path("ws/<str:case_id>/", include(case_contextualized_url_patterns)),
      path("comment/", create_comment_view, name="create_comment_view"),
      path("comment/<slug:pk>/edit", CommentUpdateView.as_view(), name="update_comment_view"),
      path("comment/<slug:pk>/delete", delete_comment_view, name="delete_comment_view"),

      # path("_auth", forward_auth, name="forward-auth_view"),

      path("cron", cron_ish_view, name='cron-jobs'),

      path("vues/<slug:component_name>.vue", vues_view, name='vues_view'),

    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# INTERNAL REST URLS
rest_patterns = [
    path("rest/", include("config.rest_router"))
]


# API URLS
api_patterns = [
    path("api/", include("config.api_router"))
]


urlpatterns += rest_patterns
urlpatterns += api_patterns

urlpatterns += [
    path('api/schema/', get_schema_view(
        title='Colander Client API',
        version="0.1.0",
        patterns=api_patterns
    ), name='api-schema'),
    # path("api/schema/", SpectacularJSONAPIView.as_view(), name="api-schema"),
    # path(
    #     "api/docs/",
    #     SpectacularSwaggerView.as_view(url_name="api-schema"),
    #     name="api-docs",
    # ),
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
