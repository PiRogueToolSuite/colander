from asgiref.sync import async_to_sync, sync_to_async
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TestCase, Client

from colander.core.models import Case
from colander.users.models import User
from config.ws_router import websocket_urlpatterns


class NotificationChannelsXssTest(TestCase):
    password = '9F7JbzWGES8hH4zWM6R1MPPCI5'
    valid_url_payload = "/drops/"
    xss_url_payload = "javascript:alert(1)"

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username='Channel User 1', password=cls.password)
        cls.case1 = Case.objects.create(name='Channel Case 1', owner=cls.user1, description='xx')

    @async_to_sync
    async def test_notification_xss(self):

        client = Client()
        await sync_to_async(client.login)(username='Channel User 1', password=self.password)

        session_key = client.cookies['sessionid'].value

        scope = {
            "type": 'websocket',
            "path": f'/ws/{str(self.case1.id)}/',
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
        self.assertTrue(connected, "Not connected")

        await communicator.send_json_to(data={ "msg": "Notification 1", "url": self.valid_url_payload, "detail": "Details 1" })
        # On user channel
        response = await communicator.receive_json_from(timeout=10)

        self.assertIn('msg', response)
        self.assertIn('detail', response)
        self.assertIn('url', response)
        self.assertEqual(response['msg'], "Notification 1")
        self.assertEqual(response['detail'], "Details 1")
        self.assertEqual(response['url'], self.valid_url_payload)

        # On case channel
        response = await communicator.receive_json_from(timeout=10)

        self.assertIn('msg', response)
        self.assertIn('detail', response)
        self.assertIn('url', response)
        self.assertEqual(response['msg'], "Notification 1")
        self.assertEqual(response['detail'], "Details 1")
        self.assertEqual(response['url'], self.valid_url_payload)


        await communicator.send_json_to(data={ "msg": "Notification 2", "url": self.xss_url_payload, "detail": "Details 2" })
        # On user channel
        response = await communicator.receive_json_from(timeout=10)

        self.assertIn('msg', response)
        self.assertIn('detail', response)
        self.assertNotIn('url', response)

        self.assertEqual(response['msg'], "Notification 2")
        self.assertEqual(response['detail'], "Details 2")

        # On case channel
        response = await communicator.receive_json_from(timeout=10)

        self.assertIn('msg', response)
        self.assertIn('detail', response)
        self.assertNotIn('url', response)

        self.assertEqual(response['msg'], "Notification 2")
        self.assertEqual(response['detail'], "Details 2")

        await communicator.disconnect()

