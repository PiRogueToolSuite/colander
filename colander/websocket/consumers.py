import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.generic.websocket import JsonWebsocketConsumer

from colander.core.models import Case


class ColanderWebSocketConsumer(JsonWebsocketConsumer):
    user = None

    def connect(self):
        new_comer = self.scope["user"]

        if not new_comer or not new_comer.is_authenticated:
            self.close()
            return

        self.user = new_comer
        if self.user_connected(self.user):
            print("Accepting user", self.user, "on channel", self.channel_layer)
            self.accept()
        else:
            self.close()

    def user_connected(self, user) -> bool:
        return False

    def disconnect(self, close_code):
        pass


class GlobalContextConsumer(ColanderWebSocketConsumer):

    def user_connected(self, user) -> bool:
        print("Colander user connected", user)
        return True

    def receive_json(self, content, **kwargs):
        print("JSON234567:", content)
        message = content["message"]

        self.send_json({"message": message})


class CaseContextConsumer(ColanderWebSocketConsumer):
    case_group_name = None
    @staticmethod
    def case_channel_name(case):
        return f"channel_{case.id}"

    @staticmethod
    def send_message_to_case_consumers(case, msg):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            CaseContextConsumer.case_channel_name(case), { 'type': 'case.message', 'message': msg }
        )
        pass

    def user_connected(self, user):
        print("Colander user connected IN CASE", user)
        case_id = self.scope['url_route']['kwargs']['case_id']
        case = Case.objects.get(pk=case_id)

        if not Case:
            print("No case")
            return False

        if not case.can_contribute(user):
            print("Can't contribute", user, case)
            return False

        self.case_group_name = CaseContextConsumer.case_channel_name(case)
        async_to_sync(self.channel_layer.group_add)(
            self.case_group_name, self.channel_name
        )
        return True

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.case_group_name, self.channel_name
        )

    def receive_json(self, content, **kwargs):
        print("JSON234567:", content)
        message = content["message"]

        self.send_json({"message": message})

        async_to_sync(self.channel_layer.group_send)(
            self.case_group_name, { 'type': 'case.message', 'message': message }
        )

    def case_message(self, event):
        message = event['message']
        self.send_json({"message": message})
