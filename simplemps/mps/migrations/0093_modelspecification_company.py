# Generated by Django 2.2.1 on 2020-10-11 15:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0092_auto_20200829_2023'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelspecification',
            name='company',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='mps.Company'),
            preserve_default=False,
        ),
    ]
