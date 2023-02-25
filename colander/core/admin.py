from django.contrib import admin

from colander.core.models import ObservableType, Observable, Case, Threat, ObservableRelation, \
    Artifact, ArtifactType, Event, Actor, EventType, Comment, PiRogueExperiment, EntityRelation


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


class EntityRelationAdmin(admin.ModelAdmin):
    pass
    # list_display = ('name', 'observable_from', 'observable_to')
    # list_filter = ('name', 'observable_from', 'observable_to')
admin.site.register(EntityRelation, EntityRelationAdmin)

