# Generated by Django 4.2.8 on 2024-12-11 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0047_alter_actortype_type_hints_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="droppedfile",
            name="target_artifact_id",
            field=models.CharField(blank=True, max_length=36, null=True),
        ),
    ]