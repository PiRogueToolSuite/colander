# Generated by Django 3.2.15 on 2022-09-29 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='type',
            field=models.CharField(choices=[('USER', 'Regular user'), ('APP', 'External application'), ('DEVICE', 'External device')], default='USER', max_length=16),
        ),
    ]
