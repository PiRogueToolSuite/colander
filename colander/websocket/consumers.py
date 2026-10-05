import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.generic.websocket import JsonWebsocketConsumer
from django.core.exceptions import ValidationError
from django.urls import resolve, Resolver404

from colander.core.models import Case

import logging
logger = logging.getLogger(__name__)


def _sanitize_notification(message):
    if isinstance(message, str):
        return message

    url = message.get("url", None)
    if url:
        try:
            resolve(url)
        except Resolver404:
            logger.warning("Notification sanitized of a non resolved url: %s", url)
            del message['url']
    return message


class ColanderWebSocketConsumer(JsonWebsocketConsumer):
    user = None

    def connect(self):
        new_comer = self.scope["user"]

        if not new_comer or not new_comer.is_authenticated:
            logger.warning("No authenticated user. Scope: %s", self.scope)
            self.close()
            return

        self.user = new_comer
        if self.user_connected(self.user):
            logger.debug("Accepting user:%s on channel:%s", self.user, self.channel_layer)
            self.accept()
        else:
            self.close()

    def user_connected(self, user) -> bool:
        return False

    def disconnect(self, close_code):
        pass


class CaseContextConsumer(ColanderWebSocketConsumer):
    case_group_name = None
    user_group_name = None

    @staticmethod
    def case_channel_name(case):
        return f"channel_case_{case.id}"

    @staticmethod
    def user_channel_name(user):
        return f"channel_user_{user.id}"

    @staticmethod
    def send_message_to_case_consumers(case, msg):
        logger.debug("colander emits a new message to case:%s", case)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            CaseContextConsumer.case_channel_name(case), { 'type': 'case.message', 'message': msg }
        )

    @staticmethod
    def send_message_to_user_consumers(user, msg):
        logger.debug("colander emits a new message to user:%s", user)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            CaseContextConsumer.user_channel_name(user), { 'type': 'user.message', 'message': msg }
        )

    def user_connected(self, user):
        logger.debug("Colander user connected IN USER:%s", user)
        self.user_group_name = CaseContextConsumer.user_channel_name(user)
        async_to_sync(self.channel_layer.group_add)(
            self.user_group_name, self.channel_name
        )

        logger.debug("Colander user:%s connected IN CASE: %s", user, self.scope['url_route']['kwargs'])
        if 'case_id' in self.scope['url_route']['kwargs']:
            case_id = self.scope['url_route']['kwargs']['case_id']

            try:
                case = Case.objects.get(pk=case_id)
            except (Case.DoesNotExist, ValidationError):
                logger.warning("No valid case id provided: %s", case_id)
                return False

            if not case.can_contribute(user):
                logger.info("User:%s can't contribute to case:%s", user, case)
                return False

            self.case_group_name = CaseContextConsumer.case_channel_name(case)
            async_to_sync(self.channel_layer.group_add)(
                self.case_group_name, self.channel_name
            )
        return True

    def disconnect(self, close_code):
        if self.user_group_name:
            async_to_sync(self.channel_layer.group_discard)(
                self.user_group_name, self.channel_name
            )

        if self.case_group_name:
            async_to_sync(self.channel_layer.group_discard)(
                self.case_group_name, self.channel_name
            )

    def receive_json(self, content, **kwargs):
        message = content

        if not message:
            logger.warning('receive_json: Incompatible message format. No message')
            return

        message = _sanitize_notification(message)

        if self.case_group_name:
            async_to_sync(self.channel_layer.group_send)(
                self.case_group_name, { 'type': 'case.message', 'message': message }
            )

        if self.user_group_name:
            async_to_sync(self.channel_layer.group_send)(
                self.user_group_name, { 'type': 'user.message', 'message': message }
            )

    def case_message(self, event):
        message = event['message']
        self.send_json(message)

    def user_message(self, event):
        message = event['message']
        self.send_json(message)

