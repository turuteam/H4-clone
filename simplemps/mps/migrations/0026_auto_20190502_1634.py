# Generated by Django 2.2rc1 on 2019-05-02 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0025_printer_is_color_device'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='managementassumption',
            name='use_non_network_margin',
        ),
        migrations.AddField(
            model_name='managementassumption',
            name='pay_non_network_commission',
            field=models.BooleanField(choices=[(True, 'Same as Commission Structure'), (False, 'None')], default=True),
        ),
        migrations.AlterField(
            model_name='managementassumption',
            name='commission_type',
            field=models.CharField(choices=[('flat_margin', 'Flat % of Margin'), ('flat_revenue', 'Flat % of Revenue'), ('blended_margin', '% of Margin - Blended Printer & Copier Rate'), ('blended_revenue', '% of Revenue - Blended Printer & Copier Rate')], default='flat_margin', max_length=40),
        ),
        migrations.AlterField(
            model_name='managementassumption',
            name='toner_after_oem_smp',
            field=models.CharField(choices=[('OEM', 'OEM'), ('REMAN', 'Reman'), ('OEM_SMP', 'OEM SMP')], default='OEM', max_length=10),
        ),
        migrations.AlterField(
            model_name='managementassumption',
            name='toner_after_reman',
            field=models.CharField(choices=[('OEM', 'OEM'), ('REMAN', 'Reman'), ('OEM_SMP', 'OEM SMP')], default='OEM_SMP', max_length=10),
        ),
    ]
