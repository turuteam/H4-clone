# Generated by Django 2.2.1 on 2019-10-05 01:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0068_managementassumption_target_margin_equipment'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='dca_password',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='dca_username',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
