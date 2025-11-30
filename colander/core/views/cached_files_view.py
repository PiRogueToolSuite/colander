import base64
import json
import uuid
from pathlib import Path

from colander_data_converter.converters.misp.converter import MISPConverter
from colander_data_converter.converters.stix2.converter import Stix2Converter
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from pymisp import MISPFeed
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer, FileField
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, \
    HTTP_413_REQUEST_ENTITY_TOO_LARGE
from rest_framework.views import APIView


class CachedFileSerializer(Serializer):
    file = FileField(required=False)
    content = CharField(required=False)
    converter = CharField(required=False)

    class Meta:
        fields = ['file', ' content', 'converter']

    def validate(self, data):
        file = data.get('file')
        content = data.get('content')
        if not file and not content:
            raise ValidationError('Either file or content is required')
        return super().validate(data)


class CachedFileApiView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CachedFileSerializer

    prefix = 'cached_file_'
    location_for_debug = Path('./tmp')

    def get(self, request, pk):
        cache_key = f"{self.prefix}{pk}"
        cached = None

        if settings.DEBUG:
            file_location = self.location_for_debug.joinpath(cache_key)
            if file_location.exists():
                with file_location.open("r") as f:
                    cached = json.load(f)
        else:
            cached = cache.get(cache_key)

        if not cached:
            return JsonResponse({"status": "failed", "message": "File not found"}, status=HTTP_404_NOT_FOUND)

        data = cached.get("data")
        decoded_data = base64.b64decode(data)
        content_type = cached.get("content_type") or "application/octet-stream"
        filename = cached.get("name") or "file"

        response = HttpResponse(decoded_data, content_type=content_type)
        response["Content-Disposition"] = f"attachment; filename=\"{filename}\""
        return response

    def convert(self, content, converter):
        if not converter:
            return content

        # Parse JSON
        try:
            content = json.loads(content)
        except (json.decoder.JSONDecodeError, Exception):
            raise Exception("Content is not valid JSON")

        if converter == "misp":
            misp_feed = MISPFeed()
            converter = MISPConverter()
            try:
                misp_feed.from_dict(**content)
            except (Exception,) as e:
                raise Exception(f"Unable to parse MISP JSON: {e}")
            try:
                feeds = converter.misp_to_colander(misp_feed)
                feed = feeds[0] if len(feeds) > 0 else None
                feed.unlink_references()
                if not feed.entities:
                    raise Exception("Invalid feed")
                return feed.model_dump(mode="json")
            except (Exception,):
                raise Exception("Unable to convert MISP Event to Colander Feed")
        elif converter == "stix2":
            converter = Stix2Converter()
            try:
                feed = converter.stix2_to_colander(content)
                feed.unlink_references()
                if not feed.entities:
                    raise Exception("Invalid feed")
                return feed.model_dump(mode="json")
            except (Exception,):
                raise Exception("Unable to convert STIX2 Bundle to Colander Feed")

        return content

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return JsonResponse(
                {"status": "failed", "message": "Either file or content is required"},
                status=HTTP_400_BAD_REQUEST
            )

        max_size = getattr(settings, "CACHED_FILE_MAX_SIZE", 20 * 1024 * 1024)  # 20 MB default

        content = serializer.validated_data.get("content")
        converter = serializer.validated_data.get("converter")
        uploaded = serializer.validated_data.get("file")

        name = getattr(uploaded, "name", "content")
        content_type = getattr(uploaded, "content_type", "text/plain")

        if content:
            size = len(content)
        else:
            try:
                size = getattr(uploaded, "size", None)
            except (Exception,):
                size = None

        if size is not None and size > max_size:
            return JsonResponse(
                {"status": "failed", "message": "File too large", "max_size": max_size},
                status=HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        if content:
            data = content.encode("utf-8")
        else:
            data = uploaded.read()
            if data is None:
                data = ""

        converter = converter if converter in ["colander", "misp", "stix2"] else None
        if converter:
            try:
                data = self.convert(data, converter)
                data = json.dumps(data).encode("utf-8")
                content_type = "application/json"
            except (Exception, ) as e:
                return JsonResponse(
                    {"status": "failed", "message": str(e)},
                    status=HTTP_400_BAD_REQUEST
                )

        if len(data) > max_size:
            return JsonResponse({
                "status": "failed",
                "message": "File too large",
                "max_size": max_size
            },
                status=HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        base64_data = base64.b64encode(data)
        uid = str(uuid.uuid4())
        cache_key = f"{self.prefix}{uid}"
        timeout = getattr(settings, "CACHED_FILE_TIMEOUT", 3600)
        cache_value = {
            "name": name,
            "content_type": content_type,
            "data": base64_data.decode(),
        }

        if settings.DEBUG:
            # Delete of cached files
            for f in self.location_for_debug.glob(f'{self.prefix}/*'):
                f.unlink()
            file_location = self.location_for_debug.joinpath(cache_key)
            with file_location.open("w") as f:
                json.dump(cache_value, f)
        else:
            cache.set(cache_key, cache_value, timeout=timeout)

        return JsonResponse({"status": "success", "uuid": uid}, status=HTTP_201_CREATED)
