# Generated by Django 2.2.4 on 2019-09-23 14:55

from django.db import migrations, models
import mps.models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0067_auto_20190923_1038'),
    ]

    operations = [
        migrations.AddField(
            model_name='managementassumption',
            name='target_margin_equipment',
            field=models.DecimalField(decimal_places=5, default=0.3, max_digits=12, validators=[mps.models.validate_proportion]),
        ),
    ]
