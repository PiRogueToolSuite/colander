# Generated by Django 3.2.15 on 2023-02-07 15:27

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_auto_20230130_1924'),
    ]

    operations = [
        migrations.AddField(
            model_name='pirogueexperiment',
            name='screencast',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pirogue_dump_screencast', to='core.artifact'),
        ),
        migrations.AlterField(
            model_name='case',
            name='es_prefix',
            field=models.CharField(default='0lu2azoqzzv4ejni', editable=False, max_length=16),
        ),
        migrations.AlterField(
            model_name='case',
            name='signing_key',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='case',
            name='verify_key',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='event',
            name='first_seen',
            field=models.DateTimeField(default=datetime.datetime(2023, 2, 7, 15, 27, 57, 67464, tzinfo=utc), help_text='First time the event has occurred.'),
        ),
        migrations.AlterField(
            model_name='event',
            name='last_seen',
            field=models.DateTimeField(default=datetime.datetime(2023, 2, 7, 15, 27, 57, 67494, tzinfo=utc), help_text='First time the event has occurred.'),
        ),
        migrations.AlterField(
            model_name='observable',
            name='es_prefix',
            field=models.CharField(default='j5gmjwu3gbaru0oe', editable=False, max_length=16),
        ),
        migrations.AlterField(
            model_name='pirogueexperiment',
            name='analysis_index',
            field=models.CharField(default='wtwpy1w6wl1umphm', help_text='Elasticsearch index storing the analysis.', max_length=64),
        ),
    ]
