from asgiref.sync import async_to_sync, sync_to_async
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TestCase, Client

from colander.core.models import Case
from colander.users.models import User
from config.ws_router import websocket_urlpatterns


# NOTE: Async tests have unstable results due to Django async/sync database management.
#       If we want to write more than on test, results are way more predictable
#       defining then into separated classes.
#       This super test class in there for this purpose only.
class BaseCampaign(TestCase):
    password = '9F7JbzWGES8hH4zWM6R1MPPCI5'

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username='Channel User 1', password=cls.password)
        cls.case1 = Case.objects.create(name='Channel Case 1', owner=cls.user1, description='xx')


class ChannelsNotAllowedToAnonymousTest(BaseCampaign):
    @async_to_sync
    async def test_anonymous_users(self):
        scope = {
            "type": 'websocket',
            "path": f'/ws/{str(self.case1.id)}/',
        }

        communicator = WebsocketCommunicator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
            scope["path"],
        )

        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected, "Connected anonymously")


class ChannelsNotAllowedToInvalidCookieTest(BaseCampaign):
    @async_to_sync
    async def test_invalid_sesssion_id(self):
        unknown_session_id = "deadbeef3m2z1y7a5b6c0d4e8f1a2b3c"
        scope = {
            "type": 'websocket',
            "path": f'/ws/{str(self.case1.id)}/',
            "headers": [(
                b"cookie",
                f"sessionid={unknown_session_id}".encode("ascii")
            )]
        }

        communicator = WebsocketCommunicator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
            scope["path"],
            headers=scope["headers"],
        )

        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected, "Connected anonymously")


class ChannelsNotAllowedToUnknownCaseIdTest(BaseCampaign):
    @async_to_sync
    async def test_invalid_case_id(self):
        client = Client()
        await sync_to_async(client.login)(username='Channel User 1', password=self.password)

        session_key = client.cookies['sessionid'].value

        scope = {
            "type": 'websocket',
            "path": f'/ws/deadbeef/',
            "headers": [(
                b"cookie",
                f"sessionid={session_key}".encode("ascii")
            )]
        }

        communicator = WebsocketCommunicator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
            scope["path"],
            headers=scope["headers"],
        )

        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected, "Connected to non existant case")

