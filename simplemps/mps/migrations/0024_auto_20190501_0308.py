# Generated by Django 2.2rc1 on 2019-05-01 03:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0023_auto_20190424_1334'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='developer',
            name='unique_developer',
        ),
        migrations.RemoveConstraint(
            model_name='drum',
            name='unique_drum',
        ),
        migrations.RemoveConstraint(
            model_name='toner',
            name='unique_toner',
        ),
        migrations.AddConstraint(
            model_name='developer',
            constraint=models.UniqueConstraint(fields=('name', 'company', 'manufacturer', 'printer', 'part_color'), name='unique_developer'),
        ),
        migrations.AddConstraint(
            model_name='drum',
            constraint=models.UniqueConstraint(fields=('name', 'company', 'manufacturer', 'printer', 'part_color'), name='unique_drum'),
        ),
        migrations.AddConstraint(
            model_name='toner',
            constraint=models.UniqueConstraint(fields=('name', 'company', 'manufacturer', 'printer', 'part_color'), name='unique_toner'),
        ),
    ]
