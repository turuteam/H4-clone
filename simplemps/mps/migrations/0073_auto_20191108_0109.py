# Generated by Django 2.2.1 on 2019-11-08 01:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0072_merge_20191108_0106'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='dca_company',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='dca_url',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
