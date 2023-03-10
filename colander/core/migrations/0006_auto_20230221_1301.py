# Generated by Django 3.2.15 on 2023-02-21 13:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0005_auto_20230217_1747'),
    ]

    operations = [
        migrations.AddField(
            model_name='entityrelation',
            name='case',
            field=models.ForeignKey(default='0bb2b589-d891-48a9-887a-bb2db2d96ba1', on_delete=django.db.models.deletion.CASCADE, related_name='core_entityrelation_related', related_query_name='core_entityrelations', to='core.case'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='entityrelation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, help_text='Creation date of this object.'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='entityrelation',
            name='owner',
            field=models.ForeignKey(default=1, help_text='Who owns this object.', on_delete=django.db.models.deletion.CASCADE, related_name='core_entityrelation_related', related_query_name='core_entityrelations', to='users.user'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='entityrelation',
            name='updated_at',
            field=models.DateTimeField(default=django.utils.timezone.now, help_text='Latest modification of this object.'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='entityrelation',
            name='name',
            field=models.CharField(help_text='Name of this relation between two entities.', max_length=512),
        ),
        migrations.AlterUniqueTogether(
            name='entityrelation',
            unique_together={('name', 'obj_from_id', 'obj_to_id')},
        ),
    ]
