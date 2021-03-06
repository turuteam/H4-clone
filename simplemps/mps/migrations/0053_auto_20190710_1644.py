# Generated by Django 2.2.1 on 2019-07-10 16:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0052_auto_20190705_1724'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeasingCompany',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leasing_company', models.CharField(max_length=100, unique=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mps.Company')),
            ],
        ),
        migrations.CreateModel(
            name='LeasingInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lease_type', models.CharField(max_length=100)),
                ('lease_term', models.IntegerField()),
                ('lease_start_range', models.DecimalField(decimal_places=4, max_digits=12)),
                ('lease_end_range', models.DecimalField(decimal_places=4, max_digits=12)),
                ('lease_rate', models.DecimalField(decimal_places=5, max_digits=10)),
                ('leasing_company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mps.LeasingCompany')),
            ],
        ),
        migrations.AddField(
            model_name='proposalpurchaseitem',
            name='lease_payment',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='proposalpurchaseitem',
            name='lease_term',
            field=models.IntegerField(default=0),
        ),
        migrations.DeleteModel(
            name='Lease',
        ),
        migrations.DeleteModel(
            name='LeaseRange',
        ),
    ]
