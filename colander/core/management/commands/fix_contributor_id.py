import uuid

from django.core.management.base import BaseCommand

from colander.users.models import User


class Command(BaseCommand):
    help = 'Fix/rotate contributor IDs.'

    def handle(self, *args, **options):
        for user in User.objects.all():
            user.contributor_id = uuid.uuid4()
            user.save()
