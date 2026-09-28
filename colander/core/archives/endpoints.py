import json
from datetime import timedelta
from functools import partial

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponse, \
    StreamingHttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.http import content_disposition_header, url_has_allowed_host_and_scheme
from rest_framework.exceptions import ValidationError

from colander.core.archives.exporters import schedule_archive_export
from colander.core.archives.serializers import model_by_super_types_str, serializers_by_model
from colander.core.models import Case, ArchiveExport, Appendix


@login_required
def case_archive_request_view(request, pk):

    case = Case.objects.get(pk=pk)

    if not case.can_contribute(request.user):
        return HttpResponseForbidden()

    archive_export = ArchiveExport.objects.create(
        case=case,
        type=Appendix.ExportType.CASE,
    )

    #archives.schedule_archive_export(archive_export)
    transaction.on_commit(partial(schedule_archive_export, archive_export))

    messages.info(request, "Archive export requested. You will be notified when done.")

    referrer = request.META.get('HTTP_REFERER')
    if referrer and url_has_allowed_host_and_scheme(referrer, allowed_hosts={request.get_host()}):
        return HttpResponseRedirect(referrer)
    return HttpResponseRedirect('/')


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


def _import_session_checks(request, model_class, kwargs):
    if "current-import-last-activity" in request.session:
        last_activity = parse_datetime(request.session["current-import-last-activity"])
        if timezone.now() > last_activity + timedelta(minutes=10):
            del request.session["current-import-last-activity"]
            if "current-import-case-id" in request.session:
                del request.session["current-import-case-id"]

    if model_class is not Case:
        if "current-import-case-id" not in request.session:
            raise Exception("No current imported case.")
        #return JsonResponse({'message': f'Unable to create entity. No imported case.'}, status=400)
        kwargs['case_id'] = request.session["current-import-case-id"]

    return kwargs


@login_required
def archives_create_entity_view(request, super_type):
    if super_type not in model_by_super_types_str:
        return JsonResponse({'message': f'{super_type} not supported'}, status=400)

    model_class = model_by_super_types_str[super_type]
    serializer_class = serializers_by_model[model_class]

    kwargs = {
        "owner": request.user,
    }

    try:
        kwargs = _import_session_checks(request, model_class, kwargs)
    except Exception as e:
        return JsonResponse({'message': f'Unable to create entity: {e}'}, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        serializer = serializer_class(data=payload, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(**kwargs)
    except ValidationError as ve:
        return JsonResponse({'message': ve.detail}, status=400)
    except Exception as e:
        return JsonResponse({'message': f'Unable to create entity: {e}'}, status=400)

    if model_class is Case:
        request.session["current-import-case-id"] = str(instance.id)
    request.session["current-import-last-activity"] = timezone.now().isoformat()

    return JsonResponse(serializer_class(instance).data)


@login_required
def archives_remap_entity_view(request, super_type, uuid):
    if super_type not in model_by_super_types_str:
        return JsonResponse({'message': f'{super_type} not supported'}, status=400)

    model_class = model_by_super_types_str[super_type]
    serializer_class = serializers_by_model[model_class]

    kwargs = {
        "owner": request.user,
    }

    try:
        kwargs = _import_session_checks(request, model_class, kwargs)
    except Exception as e:
        return JsonResponse({'message': f'Unable to create entity: {e}'}, status=400)

    try:
        instance = model_class.objects.get(pk=uuid)
    except Exception as e:
        return JsonResponse({'message': f'Unable to remap entity: {e}'}, status=404)

    if hasattr(instance, 'case'):
        modified_case = instance.case
    elif model_class is Case:
        modified_case = instance
    else:
        return JsonResponse({'message': f'Unable to remap entity: No case'}, status=400)

    if not modified_case.can_contribute(request.user):
        return JsonResponse({'message': f'Unable to remap entity'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        serializer = serializer_class(instance, data=payload, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(**kwargs)
    except ValidationError as ve:
        return JsonResponse({'message': ve.detail}, status=400)
    except Exception as e:
        return JsonResponse({'message': f'Unable to remap entity: {e}'}, status=400)

    request.session["current-import-last-activity"] = timezone.now().isoformat()

    return JsonResponse(serializer_class(instance).data)


@login_required
def archives_attach_entity_view(request, super_type, uuid):
    if super_type not in model_by_super_types_str:
        return JsonResponse({'message': f'{super_type} not supported'}, status=400)

    model_class = model_by_super_types_str[super_type]
    serializer_class = serializers_by_model[model_class]

    kwargs = {
        "owner": request.user,
    }

    try:
        kwargs = _import_session_checks(request, model_class, kwargs)
    except Exception as e:
        return JsonResponse({'message': f'Unable to create entity: {e}'}, status=400)

    try:
        instance = model_class.objects.get(pk=uuid)
    except Exception as e:
        return JsonResponse({'message': f'Unable to remap entity: {e}'}, status=404)

    if hasattr(instance, 'case'):
        modified_case = instance.case
    elif model_class is Case:
        modified_case = instance
    else:
        return JsonResponse({'message': f'Unable to remap entity: No case'}, status=400)

    if not modified_case.can_contribute(request.user):
        return JsonResponse({'message': f'Unable to remap entity'}, status=403)

    try:
        payload = request.FILES
        serializer = serializer_class(instance, data=payload, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(**kwargs)
    except ValidationError as ve:
        return JsonResponse({'message': ve.detail}, status=400)
    except Exception as e:
        return JsonResponse({'message': f'Unable to remap entity: {e}'}, status=400)

    request.session["current-import-last-activity"] = timezone.now().isoformat()

    return JsonResponse(serializer_class(instance).data)
