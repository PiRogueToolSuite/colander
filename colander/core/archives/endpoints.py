import json
from functools import partial

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponse, \
    StreamingHttpResponse
from django.utils.http import content_disposition_header
from rest_framework.exceptions import ValidationError

from colander.core.archives.exporters import schedule_archive_export
from colander.core.archives.serializers import model_by_super_types_str, serializers_by_model
from colander.core.models import Case, ArchiveExport, Appendix


@login_required
def case_archive_request_view(request, pk):

    case = Case.objects.get(pk=pk)

    archive_export = ArchiveExport.objects.create(
        case=case,
        type=Appendix.ExportType.CASE,
    )

    #archives.schedule_archive_export(archive_export)
    transaction.on_commit(partial(schedule_archive_export, archive_export))

    messages.info(request, "Archive export requested. You will be notified when done.")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def archive_takeout_view(request, pk):

    archive_export = ArchiveExport.objects.get(pk=pk)
    case = archive_export.case
    if not case.can_contribute(request.user):
        return HttpResponseForbidden()

    if archive_export.is_pending:
        response = HttpResponse(status=503)
        response.headers["Retry-After"] = "120" # 2 minutes
        return response

    response = StreamingHttpResponse(archive_export.file, content_type='application/zip')
    response['Content-Disposition'] = content_disposition_header(
        True,
        archive_export.filename
    )

    return response


@login_required
def archives_check_uuid_view(request, super_type, uuid):
    if super_type not in model_by_super_types_str:
        return JsonResponse({'message': f'{super_type} not supported'}, status=400)
    model_class = model_by_super_types_str[super_type]
    if model_class.objects.filter(pk=uuid).exists():
        return JsonResponse({'message': 'uuid exists'}, status=200)
    else:
        return JsonResponse({'message': 'uuid does not exist'}, status=404)


@login_required
def archives_create_entity_view(request, super_type):
    if super_type not in model_by_super_types_str:
        return JsonResponse({'message': f'{super_type} not supported'}, status=400)

    model_class = model_by_super_types_str[super_type]
    serializer_class = serializers_by_model[model_class]

    try:
        payload = json.loads(request.body.decode('utf-8'))
        serializer = serializer_class(data=payload, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(owner=request.user)
        return JsonResponse(serializer_class(instance).data)
    except ValidationError as ve:
        return JsonResponse({'message': ve.detail}, status=400)
    except Exception as e:
        return JsonResponse({'message': f'Unable to create entity: {e}'}, status=400)


@login_required
def archives_remap_entity_view(request, super_type, uuid):
    if super_type not in model_by_super_types_str:
        return JsonResponse({'message': f'{super_type} not supported'}, status=400)

    model_class = model_by_super_types_str[super_type]
    serializer_class = serializers_by_model[model_class]

    try:
        instance = model_class.objects.get(pk=uuid)
        payload = json.loads(request.body.decode('utf-8'))
        serializer = serializer_class(instance, data=payload, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return JsonResponse(serializer_class(instance).data)
    except ValidationError as ve:
        return JsonResponse({'message': ve.detail}, status=400)
    except Exception as e:
        return JsonResponse({'message': f'Unable to remap entity: {e}'}, status=400)


@login_required
def archives_attach_entity_view(request, super_type, uuid):
    if super_type not in model_by_super_types_str:
        return JsonResponse({'message': f'{super_type} not supported'}, status=400)

    model_class = model_by_super_types_str[super_type]
    serializer_class = serializers_by_model[model_class]

    try:
        instance = model_class.objects.get(pk=uuid)
        payload = request.FILES
        serializer = serializer_class(instance, data=payload, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return JsonResponse(serializer_class(instance).data)
    except ValidationError as ve:
        return JsonResponse({'message': ve.detail}, status=400)
    except Exception as e:
        return JsonResponse({'message': f'Unable to remap entity: {e}'}, status=400)
