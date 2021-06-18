# Generated by Django 2.2.1 on 2019-08-31 02:19

from django.db import migrations, models
import mps.models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0061_auto_20190826_2218'),
    ]

    operations = [
        migrations.AddField(
            model_name='managementassumption',
            name='allow_cartridge_pricing',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='managementassumption',
            name='allow_leasing',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='managementassumption',
            name='allow_reman',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='managementassumption',
            name='allow_tiered',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='managementassumption',
            name='tier2_inflate',
            field=models.DecimalField(decimal_places=5, default=0.2, max_digits=12, validators=[mps.models.validate_proportion]),
        ),
        migrations.AddField(
            model_name='managementassumption',
            name='tier3_inflate',
            field=models.DecimalField(decimal_places=5, default=0.3, max_digits=12, validators=[mps.models.validate_proportion]),
        ),
        migrations.AddField(
            model_name='printer',
            name='avm_color',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AddField(
            model_name='printer',
            name='avm_mono',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AlterField(
            model_name='pagecost',
            name='source',
            field=models.CharField(choices=[('fixed', 'Fixed'), ('local', 'Local')], max_length=8),
        ),
    ]