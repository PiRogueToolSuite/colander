from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe

from colander.core.forms import EntityRelationForm
from colander.core.models import EntityRelation
from colander.core.views.views import get_active_case


@login_required
def create_or_edit_entity_relation_view(request):
    active_case = get_active_case(request)
    if not active_case:
        return redirect('collect_case_create_view')
    form = EntityRelationForm()
    entities = active_case.get_all_entities(exclude_types=['Case', 'EntityRelation'])
    choices = [
        (t.id, mark_safe(f'{t.value} - {t._meta.verbose_name}'))
        for t in entities
    ]
    form.fields['obj_from'].choices = choices
    form.fields['obj_to'].choices = choices
    if request.method == 'POST':
        form = EntityRelationForm(request.POST)
        form.fields['obj_from'].choices = choices
        form.fields['obj_to'].choices = choices
        if form.is_valid():
            name = form.cleaned_data.get('name')
            obj_from = None
            obj_to = None
            obj_from_id = form.cleaned_data.get('obj_from')
            obj_to_id = form.cleaned_data.get('obj_to')
            for entity in entities:
                if str(entity.id) == obj_from_id:
                    obj_from = entity
                if str(entity.id) == obj_to_id:
                    obj_to = entity
            if active_case == obj_from.case and active_case == obj_to.case:
                relation = EntityRelation(
                    name=name,
                    case=active_case,
                    owner=request.user,
                    obj_from_id=obj_from_id,
                    obj_from_type=ContentType.objects.get(app_label='core', model=obj_from.super_type.lower()),
                    obj_to_id=obj_to_id,
                    obj_to_type=ContentType.objects.get(app_label='core', model=obj_to.super_type.lower()),
                )
                try:
                    relation.full_clean()
                    relation.save()
                except ValidationError as e:
                    messages.info(request, 'This relation already exists.', extra_tags='danger')
            else:
                messages.info(request, 'The two entities have to belong to the active case.', extra_tags='danger')

    relations = EntityRelation.get_user_entity_relations(request.user, active_case)
    return render(
        request,
        'pages/collect/entity_relations.html',
        {
            'relations': relations,
            'form': form
        }
    )


@login_required
def delete_relation_view(request, pk):
    obj = EntityRelation.objects.get(id=pk)
    obj.delete()
    return redirect("collect_entity_relation_create_view")
