# Generated by Django 2.2.1 on 2019-06-20 21:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0047_add_default_cpp_tiers_to_assumptions'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposal',
            name='bln_base_rate_color',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='bln_base_rate_mono',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='bln_base_rate_mono_on_color',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='bln_base_volume_color',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='bln_base_volume_mono',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='bln_base_volume_mono_on_color',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='bln_proposed_price_color',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='bln_proposed_price_mono',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='bln_proposed_price_mono_on_color',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='bln_rcmd_price_color',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='bln_rcmd_price_mono',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='bln_rcmd_price_mono_on_color',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=12, null=True),
        ),
    ]