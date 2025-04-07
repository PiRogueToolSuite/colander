# Generated by Django 4.2.8 on 2025-02-04 13:43

import colander.core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0051_subgraph"),
    ]

    operations = [
        migrations.AddField(
            model_name="entity",
            name="thumbnail",
            field=models.FileField(
                blank=True, max_length=512, null=True, upload_to=colander.core.models._get_entity_thumbnails_storage_dir
            ),
        ),
    ]
