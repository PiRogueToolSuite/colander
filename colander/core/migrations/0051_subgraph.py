# Generated by Django 4.2.8 on 2025-01-15 14:33

import colander.core.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0050_alter_entity_source_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubGraph",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier.",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        default="",
                        help_text="Give a meaningful name to this SubGraph.",
                        max_length=512,
                        verbose_name="name",
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, help_text="Add more details about this SubGraph.", null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, help_text="Creation date of this object.")),
                ("updated_at", models.DateTimeField(auto_now=True, help_text="Latest modification of this object.")),
                ("overrides", models.JSONField(blank=True, null=True)),
                (
                    "thumbnail",
                    models.FileField(
                        blank=True,
                        max_length=512,
                        null=True,
                        upload_to=colander.core.models._get_subgraph_thumbnails_storage_dir,
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_related",
                        related_query_name="%(app_label)s_%(class)ss",
                        to="core.case",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        help_text="Who owns this object.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_related",
                        related_query_name="%(app_label)s_%(class)ss",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
