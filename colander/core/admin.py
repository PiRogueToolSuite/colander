from django.contrib import admin

from colander.core.models import (
    Actor,
    Artifact,
    ArtifactType,
    BackendCredentials,
    Case,
    ColanderTeam,
    Comment,
    DetectionRule,
    DetectionRuleOutgoingFeed,
    DroppedFile,
    EntityOutgoingFeed,
    EntityRelation,
    Event,
    EventType,
    Observable,
    ObservableRelation,
    ObservableType,
    PiRogueExperiment,
    Threat,
    UploadRequest, SubGraph,
)


class ColanderTeamAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)
admin.site.register(ColanderTeam, ColanderTeamAdmin)


class ArtifactTypeAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'name', 'description')
    list_filter = ('name', 'description')
admin.site.register(ArtifactType, ArtifactTypeAdmin)


class ObservableTypeAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'name', 'description')
    list_filter = ('name', 'description')
admin.site.register(ObservableType, ObservableTypeAdmin)


class ObservableAdmin(admin.ModelAdmin):
    list_display = ('type', 'value', 'description')
    list_filter = ('type', 'description')
admin.site.register(Observable, ObservableAdmin)


class ArtifactAdmin(admin.ModelAdmin):
    list_display = ('type', 'sha256')
    list_filter = ('type', 'sha256')
admin.site.register(Artifact, ArtifactAdmin)


class CaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    list_filter = ('name', 'owner')
admin.site.register(Case, CaseAdmin)


class CommentAdmin(admin.ModelAdmin):
    pass
admin.site.register(Comment, CommentAdmin)


class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'name')
    list_filter = ('short_name', 'name')
admin.site.register(EventType, EventTypeAdmin)


class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    list_filter = ('name', 'owner')
admin.site.register(Event, EventAdmin)


class ThreatAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    list_filter = ('name', 'type')
admin.site.register(Threat, ThreatAdmin)


class ActorAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    list_filter = ('name', 'type')
admin.site.register(Actor, ActorAdmin)


class PiRogueExperimentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)
admin.site.register(PiRogueExperiment, PiRogueExperimentAdmin)


class ObservableRelationAdmin(admin.ModelAdmin):
    list_display = ('name', 'observable_from', 'observable_to')
    list_filter = ('name', 'observable_from', 'observable_to')
admin.site.register(ObservableRelation, ObservableRelationAdmin)


class DetectionRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    list_filter = ('name', 'type')
admin.site.register(DetectionRule, DetectionRuleAdmin)


class EntityRelationAdmin(admin.ModelAdmin):
    pass
    # list_display = ('name', 'observable_from', 'observable_to')
    # list_filter = ('name', 'observable_from', 'observable_to')
admin.site.register(EntityRelation, EntityRelationAdmin)


class BackendCredentialsAdmin(admin.ModelAdmin):
    list_display = ('backend',)
    # list_filter = ('name', 'observable_from', 'observable_to')
admin.site.register(BackendCredentials, BackendCredentialsAdmin)


class UploadRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at', 'status')
    # list_filter = ('name', 'observable_from', 'observable_to')
admin.site.register(UploadRequest, UploadRequestAdmin)


class EntityOutFeedAdmin(admin.ModelAdmin):
    list_display = ('name',)
admin.site.register(EntityOutgoingFeed, EntityOutFeedAdmin)


class DetectionRuleOutFeedAdmin(admin.ModelAdmin):
    list_display = ('name',)
admin.site.register(DetectionRuleOutgoingFeed, DetectionRuleOutFeedAdmin)


class DroppedFileAdmin(admin.ModelAdmin):
    list_display = ('owner', 'dropped_at', 'case', 'filename', 'mime_type')
admin.site.register(DroppedFile, DroppedFileAdmin)


class SubGraphAdmin(admin.ModelAdmin):
    list_display = ('owner', 'created_at', 'case', 'name')
admin.site.register(SubGraph, SubGraphAdmin)
