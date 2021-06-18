# Generated by Django 2.2rc1 on 2019-05-03 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0027_auto_20190503_1755'),
    ]

    operations = [
        migrations.AlterField(
            model_name='developer',
            name='part_color',
            field=models.CharField(choices=[('mono', 'Black'), ('cyan', 'Cyan'), ('yellow', 'Yellow'), ('magenta', 'Magenta')], max_length=25),
        ),
        migrations.AlterField(
            model_name='drum',
            name='part_color',
            field=models.CharField(choices=[('mono', 'Black'), ('cyan', 'Cyan'), ('yellow', 'Yellow'), ('magenta', 'Magenta')], max_length=25),
        ),
        migrations.AlterField(
            model_name='streetfighterdeveloper',
            name='requested_price',
            field=models.DecimalField(decimal_places=5, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='streetfighterdrum',
            name='requested_price',
            field=models.DecimalField(decimal_places=5, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='streetfightertoner',
            name='requested_price',
            field=models.DecimalField(decimal_places=5, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='toner',
            name='part_color',
            field=models.CharField(choices=[('mono', 'Black'), ('cyan', 'Cyan'), ('yellow', 'Yellow'), ('magenta', 'Magenta')], max_length=25),
        ),
    ]
