# Generated by Django 2.2.4 on 2020-05-17 21:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0084_proposalpurchaseitem_lease_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='managementassumption',
            name='allow_rental',
            field=models.BooleanField(default=False),
        ),
    ]
