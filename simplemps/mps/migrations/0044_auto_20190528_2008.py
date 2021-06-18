# Generated by Django 2.2.1 on 2019-05-28 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0043_merge_20190523_1402'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='compatible',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='status',
            field=models.CharField(default='', max_length=8),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='proposalserviceitem',
            name='tier_level_color',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='proposalserviceitem',
            name='tier_level_mono',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
