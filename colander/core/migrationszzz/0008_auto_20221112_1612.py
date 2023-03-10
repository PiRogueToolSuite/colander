# Generated by Django 3.2.15 on 2022-11-12 16:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20221112_1529'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observablerelation',
            name='observable_from',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='relation_origins', to='core.observable'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='observablerelation',
            name='observable_to',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='relation_targets', to='core.observable'),
            preserve_default=False,
        ),
    ]
