import hashlib
import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404

from colander.core.models import UploadRequest
from colander.core.serializers.upload_request_serializers import UploadRequestSerializer


logger = logging.getLogger(__name__)


@login_required
def initialize_upload(request):
    if request.method == 'POST':
        payload = json.loads(request.body.decode('utf-8'))
        serializer = UploadRequestSerializer(data=payload, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(owner=request.user)
            return JsonResponse(UploadRequestSerializer(instance).data)
        except ValidationError as ve:
            return JsonResponse({'message': ve.messages}, status=500)
        except Exception as e:
            return JsonResponse({'message': f"Unable to create upload: {e}"}, status=500)
    else:
        return JsonResponse({'message': 'Method not allowed'}, status=405)


@login_required
def append_to_upload(request, upload_id):
    upload_request = get_object_or_404(UploadRequest, id=upload_id)

    if request.method == 'GET':
        response = JsonResponse(UploadRequestSerializer(upload_request).data)
        return response

    if request.method == 'POST':
        payload = request.POST.copy()
        if 'file' in request.FILES:
            payload['file'] = request.FILES['file']
        serializer = UploadRequestSerializer(upload_request, data=payload, partial=True, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return JsonResponse(UploadRequestSerializer(instance).data)
        except ValidationError as ve:
            upload_request.status = UploadRequest.Status.FAILED
            upload_request.save()
            return JsonResponse({'message': ve.messages}, status=500)
        except Exception as e:
            upload_request.status = UploadRequest.Status.FAILED
            upload_request.save()
            return JsonResponse({'message': f"Unable to update upload: {e}"}, status=500)
