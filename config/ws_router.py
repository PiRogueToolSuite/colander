from django.urls import re_path, path

from colander.websocket.consumers import CaseContextConsumer

websocket_urlpatterns = [
    #path('global/', GlobalContextConsumer.as_asgi()),
    re_path(r'(ws/(?P<case_id>[0-9A-Fa-f-]+)/)?.*', CaseContextConsumer.as_asgi()),
]
