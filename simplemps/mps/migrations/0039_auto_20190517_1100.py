# Generated by Django 2.2.1 on 2019-05-17 11:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0038_auto_20190509_1926'),
    ]

    operations = [
        migrations.RenameField(
            model_name='accessory',
            old_name='name',
            new_name='description',
        ),
        migrations.RemoveField(
            model_name='accessory',
            name='cost',
        ),
        migrations.AddField(
            model_name='accessory',
            name='msrp_cost',
            field=models.DecimalField(decimal_places=4, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='accessory',
            name='out_cost',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=9),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='accessory',
            name='printer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mps.Printer'),
        ),
    ]
