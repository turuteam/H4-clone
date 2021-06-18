# Generated by Django 2.2rc1 on 2019-05-04 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0030_auto_20190504_1640'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='manageralert',
            name='resolved',
        ),
        migrations.AddConstraint(
            model_name='streetfighterdeveloper',
            constraint=models.UniqueConstraint(fields=('proposal', 'company', 'printer', 'part_color'), name='unique_sf_developer'),
        ),
        migrations.AddConstraint(
            model_name='streetfighterdrum',
            constraint=models.UniqueConstraint(fields=('proposal', 'company', 'printer', 'part_color'), name='unique_sf_drum'),
        ),
        migrations.AddConstraint(
            model_name='streetfightertoner',
            constraint=models.UniqueConstraint(fields=('proposal', 'company', 'printer', 'part_color'), name='unique_sf_toner'),
        ),
    ]
