# Generated by Django 4.2.8 on 2024-12-13 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0049_droppedfile_mime_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="entity",
            name="source_url",
            field=models.URLField(
                blank=True,
                help_text="Specify the source of this object.",
                max_length=2048,
                null=True,
                verbose_name="Source URL",
            ),
        ),
    ]
