# Generated by Django 3.2.15 on 2022-12-11 14:11

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_auto_20221211_1410'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='es_prefix',
            field=models.CharField(default='4p2wqllpjtmb8va2', editable=False, max_length=16),
        ),
        migrations.AlterField(
            model_name='event',
            name='first_seen',
            field=models.DateTimeField(default=datetime.datetime(2022, 12, 11, 14, 11, 33, 126484, tzinfo=utc), help_text='First time the event has occurred.'),
        ),
        migrations.AlterField(
            model_name='event',
            name='last_seen',
            field=models.DateTimeField(default=datetime.datetime(2022, 12, 11, 14, 11, 33, 126511, tzinfo=utc), help_text='First time the event has occurred.'),
        ),
        migrations.AlterField(
            model_name='observable',
            name='es_prefix',
            field=models.CharField(default='yo2ppu69x650g04b', editable=False, max_length=16),
        ),
    ]
