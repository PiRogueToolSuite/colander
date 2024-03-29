# Generated by Django 3.2.18 on 2023-06-01 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0029_alter_entityoutgoingfeed_content_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='outgoingfeed',
            old_name='password',
            new_name='secret',
        ),
        migrations.AlterField(
            model_name='entityoutgoingfeed',
            name='content_type',
            field=models.ManyToManyField(limit_choices_to={'app_label': 'colander_models', 'model__in': ['actor', 'artifact', 'device', 'observable', 'threat']}, related_name='entity_out_feed_types', to='contenttypes.ContentType'),
        ),
    ]
