# Generated by Django 2.2rc1 on 2019-05-06 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0033_auto_20190504_2157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='streetfighterdeveloper',
            name='new_price',
            field=models.DecimalField(decimal_places=5, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='streetfighterdrum',
            name='new_price',
            field=models.DecimalField(decimal_places=5, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='streetfightertoner',
            name='new_price',
            field=models.DecimalField(decimal_places=5, max_digits=10, null=True),
        ),
    ]
