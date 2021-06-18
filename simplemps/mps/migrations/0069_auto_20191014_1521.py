# Generated by Django 2.2.4 on 2019-10-14 19:21

from django.db import migrations, models
import mps.models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0068_managementassumption_target_margin_equipment'),
    ]

    operations = [
        migrations.AddField(
            model_name='managementassumption',
            name='allow_term_offsets',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='managementassumption',
            name='cost_offset_12month',
            field=models.DecimalField(decimal_places=5, default=0.0, max_digits=12, validators=[mps.models.validate_proportion]),
        ),
        migrations.AddField(
            model_name='managementassumption',
            name='cost_offset_24month',
            field=models.DecimalField(decimal_places=5, default=0.0, max_digits=12, validators=[mps.models.validate_proportion]),
        ),
        migrations.AddField(
            model_name='managementassumption',
            name='cost_offset_36month',
            field=models.DecimalField(decimal_places=5, default=0.0, max_digits=12, validators=[mps.models.validate_proportion]),
        ),
        migrations.AddField(
            model_name='managementassumption',
            name='cost_offset_48month',
            field=models.DecimalField(decimal_places=5, default=0.0, max_digits=12, validators=[mps.models.validate_proportion]),
        ),
        migrations.AddField(
            model_name='managementassumption',
            name='cost_offset_60month',
            field=models.DecimalField(decimal_places=5, default=0.0, max_digits=12, validators=[mps.models.validate_proportion]),
        ),
    ]
