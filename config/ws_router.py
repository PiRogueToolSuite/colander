from django.urls import re_path, path

from colander.websocket.consumers import GlobalContextConsumer, CaseContextConsumer

websocket_urlpatterns = [
    path("ws/global/", GlobalContextConsumer.as_asgi()),
    path("ws/case/<slug:case_id>/", CaseContextConsumer.as_asgi()),
]
