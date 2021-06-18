# Generated by Django 2.2.3 on 2019-07-19 18:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0053_auto_20190710_1644'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageCost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(max_length=32)),
                ('service_cpp', models.DecimalField(decimal_places=4, max_digits=10)),
                ('service_cpp_cmp', models.DecimalField(decimal_places=4, max_digits=10, null=True)),
                ('supply_cpp_oem_mono', models.DecimalField(decimal_places=4, max_digits=10, null=True)),
                ('supply_cpp_oem_color', models.DecimalField(decimal_places=4, max_digits=10, null=True)),
                ('supply_cpp_smp_mono', models.DecimalField(decimal_places=4, max_digits=10, null=True)),
                ('supply_cpp_smp_color', models.DecimalField(decimal_places=4, max_digits=10, null=True)),
                ('supply_cpp_cmp_mono', models.DecimalField(decimal_places=4, max_digits=10, null=True)),
                ('supply_cpp_cmp_color', models.DecimalField(decimal_places=4, max_digits=10, null=True)),
                ('currency', models.CharField(max_length=32)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=128)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('updated_by', models.CharField(max_length=128)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mps.Company')),
                ('printer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mps.Printer')),
            ],
        ),
    ]
