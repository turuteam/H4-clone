# Generated by Django 2.2.1 on 2019-05-22 15:00

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0039_auto_20190517_1100'),
    ]

    operations = [
        migrations.AddField(
            model_name='printer',
            name='display_description',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oem_number', models.CharField(max_length=100, null=True)),
                ('product_type', models.CharField(max_length=16)),
                ('display_description', models.CharField(max_length=64, null=True)),
                ('long_description', models.CharField(max_length=250)),
                ('dca_description', models.CharField(max_length=128, null=True)),
                ('colorant', models.CharField(max_length=25, null=True)),
                ('product_yield', models.IntegerField(null=True)),
                ('msrp', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=10)),
                ('currency', models.CharField(max_length=32, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_created', to='mps.MPS_User')),
                ('make', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mps.Make')),
                ('printer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mps.Printer')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_updated', to='mps.MPS_User')),
            ],
        ),
    ]
