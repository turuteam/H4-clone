# Generated by Django 2.2.1 on 2020-02-01 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0076_merge_20200201_1541'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposaltcoitem',
            name='monthly_lease_payment',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='monthly_lease',
            field=models.DecimalField(blank=True, decimal_places=5, default=0, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='mps_price',
            field=models.DecimalField(blank=True, decimal_places=5, default=0, max_digits=12, null=True),
        ),
    ]
