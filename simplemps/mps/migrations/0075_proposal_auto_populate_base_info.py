# Generated by Django 2.2.4 on 2019-12-04 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0074_merge_20191108_1751'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposal',
            name='auto_populate_base_info',
            field=models.BooleanField(default=True),
        ),
    ]