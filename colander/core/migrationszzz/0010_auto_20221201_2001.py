# Generated by Django 3.2.15 on 2022-12-01 20:01

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0009_artifact_extracted_from'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='actor',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='commonmodel',
            options={'ordering': ['-updated_at']},
        ),
        migrations.AlterModelOptions(
            name='observable',
            options={},
        ),
        migrations.AlterField(
            model_name='comment',
            name='content',
            field=models.TextField(default='No description', help_text='Add more details about the comment.'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, help_text='Creation date of the comment.'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique identifier of the comment.', primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='comment',
            name='owner',
            field=models.ForeignKey(help_text='Who redacted this comment.', on_delete=django.db.models.deletion.CASCADE, related_name='comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='comment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, help_text='Latest modification of the comment.'),
        ),
        migrations.AlterField(
            model_name='event',
            name='count',
            field=models.BigIntegerField(default=0, help_text='How many times this event has occurred.'),
        ),
        migrations.AlterField(
            model_name='event',
            name='detected_by',
            field=models.ForeignKey(blank=True, help_text='Select the rule which has detected this event.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='core.detectionrule'),
        ),
        migrations.AlterField(
            model_name='event',
            name='extracted_from',
            field=models.ForeignKey(blank=True, help_text='Select the artifact from which this event was extracted.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='core.artifact'),
        ),
        migrations.AlterField(
            model_name='event',
            name='first_seen',
            field=models.DateTimeField(default=datetime.datetime(2022, 12, 1, 20, 1, 38, 160668, tzinfo=utc), help_text='First time the event has occurred.'),
        ),
        migrations.AlterField(
            model_name='event',
            name='involved_observables',
            field=models.ManyToManyField(help_text='Select the observables involved with this event.', related_name='events', to='core.Observable'),
        ),
        migrations.AlterField(
            model_name='event',
            name='last_seen',
            field=models.DateTimeField(default=datetime.datetime(2022, 12, 1, 20, 1, 38, 160701, tzinfo=utc), help_text='First time the event has occurred.'),
        ),
        migrations.AlterField(
            model_name='event',
            name='observed_on',
            field=models.ForeignKey(blank=True, help_text='Select the device on which this event was observed.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='core.device'),
        ),
        migrations.CreateModel(
            name='Relationship',
            fields=[
                ('commonmodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.commonmodel')),
                ('name', models.CharField(help_text='Name of this relation between two entities.', max_length=512)),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='core_relationship_related', related_query_name='core_relationships', to='core.case')),
                ('obj_from', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relation_from', to='core.commonmodel')),
                ('obj_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relation_to', to='core.commonmodel')),
            ],
            options={
                'ordering': ['-updated_at'],
            },
            bases=('core.commonmodel', models.Model),
        ),
        migrations.CreateModel(
            name='ObservableAnalysisEngine',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique identifier.', primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=512)),
                ('description', models.TextField(blank=True, help_text='Add more details about this engine.', null=True)),
                ('source_url', models.URLField(blank=True, help_text='Specify the link to this engine.', null=True, verbose_name='Source URL')),
                ('observable_type', models.ForeignKey(help_text='Type of observable this engine can handle.', on_delete=django.db.models.deletion.CASCADE, to='core.observabletype')),
            ],
        ),
    ]
