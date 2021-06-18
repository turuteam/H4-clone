# Generated by Django 2.2.1 on 2019-05-09 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0037_auto_20190509_1906'),
    ]

    operations = [
        migrations.AlterField(
            model_name='streetfighterdeveloper',
            name='new_price',
            field=models.DecimalField(blank=True, decimal_places=5, default=None, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='streetfighterdeveloper',
            name='requested_price',
            field=models.DecimalField(blank=True, decimal_places=5, default=None, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='streetfighterdrum',
            name='new_price',
            field=models.DecimalField(blank=True, decimal_places=5, default=None, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='streetfighterdrum',
            name='requested_price',
            field=models.DecimalField(blank=True, decimal_places=5, default=None, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='streetfightertoner',
            name='new_price',
            field=models.DecimalField(blank=True, decimal_places=5, default=None, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='streetfightertoner',
            name='requested_price',
            field=models.DecimalField(blank=True, decimal_places=5, default=None, max_digits=10, null=True),
        ),
    ]