from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Q

from colander.core.models import EntityRelation, Entity


class Command(BaseCommand):
    help = 'Fix entity relations containing defaced entity type from/to'
    output_transaction = True

    def handle(self, *args, **options):
        entity_ct = ContentType.objects.get(app_label='core', model='entity')
        defacedRelations = EntityRelation.objects.filter(
            Q(obj_from_type=entity_ct.id) |
            Q(obj_to_type=entity_ct.id)
        )

        if len(defacedRelations) == 0:
            print("No 'buggy' entity relation to fix. Done.")
        else:
            for er in defacedRelations:
                print("Upgrading entity relation to concrete", er)
                print("        from_id", er.obj_from_id)
                print("          to_id", er.obj_to_id)
                defaced_from = Entity.objects.get(pk=er.obj_from_id)
                defaced_to = Entity.objects.get(pk=er.obj_to_id)
                print("           from", defaced_from)
                print("             to", defaced_to)
                concrete_from = defaced_from.concrete()
                concrete_to = defaced_to.concrete()
                print("  concrete from", concrete_from)
                print("    concrete to", concrete_to)
                er.obj_from = concrete_from
                er.obj_to = concrete_to
                er.save()
                print("         status", " fixed.")
                
            print("Entity relations fixed:", len(defacedRelations), "Done.")

