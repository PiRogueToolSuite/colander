# Generated by Django 3.2.15 on 2022-12-11 12:39

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20221201_2010'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='es_prefix',
            field=models.CharField(default='np744gnjakyl6yc7', editable=False, max_length=16),
        ),
        migrations.AlterField(
            model_name='artifact',
            name='extracted_from',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='artifacts', to='core.device'),
        ),
        migrations.AlterField(
            model_name='event',
            name='first_seen',
            field=models.DateTimeField(default=datetime.datetime(2022, 12, 11, 12, 39, 14, 511055, tzinfo=utc), help_text='First time the event has occurred.'),
        ),
        migrations.AlterField(
            model_name='event',
            name='last_seen',
            field=models.DateTimeField(default=datetime.datetime(2022, 12, 11, 12, 39, 14, 511097, tzinfo=utc), help_text='First time the event has occurred.'),
        ),
    ]
