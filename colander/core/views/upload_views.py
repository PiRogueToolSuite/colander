from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
import json
from colander.core.models import UploadRequest
from colander.core.serializers.upload_request_serializers import UploadRequestSerializer
import logging
import hashlib

logger = logging.getLogger(__name__)

@login_required
def initialize_upload(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
            file_size = int(payload.get('file_size'))
            upload_request = UploadRequest(
                owner=request.user,
                size=file_size,
                name=payload.get('file_name'),
                chunks=payload.get('chunks'),
                status=UploadRequest.Status.PROCESSING
            )
            upload_request.save()
            try:
                with open(upload_request.path, 'wb') as f:
                    f.seek(file_size - 1)
                    f.write(b'\0')
            except IOError as e:
                error_message = "Unable to create file: {}".format(e)
                logger.error(error_message, exc_info=True)
                upload_request.cleanup()
                upload_request.status = UploadRequest.Status.FAILED
                upload_request.save()
                return JsonResponse({'message': error_message}, status=500)
            return JsonResponse(UploadRequestSerializer(upload_request).data)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@login_required
def append_to_upload(request, upload_id):
    upload_request = get_object_or_404(UploadRequest, id=upload_id)
    if request.method == 'GET':
        response = JsonResponse(UploadRequestSerializer(upload_request).data)
        return response
    if request.method == 'POST':
        file = request.FILES['file'].read()
        addr = int(request.POST['addr'])
        # Get chunk digest from DB
        if str(addr) not in upload_request.chunks:
            return JsonResponse({'message': f'Chunk {addr} not found'}, status=500)
        chunk_hash = upload_request.chunks.get(str(addr))
        # Compute chunk SHA256
        sha256 = hashlib.sha256(file).hexdigest()
        print(f'@ {addr} stored {chunk_hash} received {sha256}')
        print(f'@ {addr} stored {chunk_hash} received {sha256}')
        if chunk_hash == sha256:
            upload_request.chunks.pop(str(addr))
        else:
            upload_request.eof = False
            upload_request.next_addr = -2
            upload_request.status = UploadRequest.Status.FAILED
            upload_request.save()
            upload_request.cleanup()
            return JsonResponse({'message': f'Corrupted chunk @ {addr}'}, status=500)

        with open(upload_request.path, mode='r+b') as destination:
            destination.seek(int(addr))
            destination.write(file)
            destination.flush()

        if len(upload_request.chunks) > 0:
            upload_request.next_addr = list(upload_request.chunks.keys())[0]
        else:
            upload_request.eof = True
            upload_request.next_addr = -1
            upload_request.status = UploadRequest.Status.SUCCEEDED
            upload_request.save()

        upload_request.save()
        response = UploadRequestSerializer(upload_request).data
        return JsonResponse(response)
