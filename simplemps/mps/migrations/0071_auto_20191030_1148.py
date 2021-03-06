# Generated by Django 2.2.4 on 2019-10-30 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0070_auto_20191014_2032'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagecost',
            name='def_base_rate_color',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='pagecost',
            name='def_base_rate_mono',
            field=models.DecimalField(blank=True, decimal_places=5, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='pagecost',
            name='def_base_volume_color',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='pagecost',
            name='def_base_volume_mono',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
