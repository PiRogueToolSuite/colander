# Generated by Django 3.2.18 on 2023-06-03 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0034_auto_20230602_0857'),
    ]

    operations = [
        migrations.AddField(
            model_name='actortype',
            name='stix2_pattern',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='actortype',
            name='stix2_pattern_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='actortype',
            name='stix2_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='actortype',
            name='stix2_value_field_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='artifacttype',
            name='stix2_pattern',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='artifacttype',
            name='stix2_pattern_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='artifacttype',
            name='stix2_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='artifacttype',
            name='stix2_value_field_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='detectionruletype',
            name='stix2_pattern',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='detectionruletype',
            name='stix2_pattern_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='detectionruletype',
            name='stix2_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='detectionruletype',
            name='stix2_value_field_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='devicetype',
            name='stix2_pattern',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='devicetype',
            name='stix2_pattern_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='devicetype',
            name='stix2_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='devicetype',
            name='stix2_value_field_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='eventtype',
            name='stix2_pattern',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='eventtype',
            name='stix2_pattern_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='eventtype',
            name='stix2_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='eventtype',
            name='stix2_value_field_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='observabletype',
            name='stix2_pattern',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='observabletype',
            name='stix2_pattern_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='observabletype',
            name='stix2_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='observabletype',
            name='stix2_value_field_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='threattype',
            name='stix2_pattern',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='threattype',
            name='stix2_pattern_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='threattype',
            name='stix2_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='threattype',
            name='stix2_value_field_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
