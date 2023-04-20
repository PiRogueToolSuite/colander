# Generated by Django 3.2.18 on 2023-04-20 08:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0016_uploadrequest_target_artifact_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entityrelation',
            name='obj_from_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='obj_from_types', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='entityrelation',
            name='obj_to_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='obj_to_types', to='contenttypes.contenttype'),
        ),
    ]
