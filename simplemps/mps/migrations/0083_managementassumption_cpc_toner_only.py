# Generated by Django 2.2.4 on 2020-04-08 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0082_managementassumption_supplies_only'),
    ]

    operations = [
        migrations.AddField(
            model_name='managementassumption',
            name='cpc_toner_only',
            field=models.BooleanField(default=True),
        ),
    ]
