# Generated by Django 2.2rc1 on 2019-05-04 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0029_proposal_create_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='streetfighterdeveloper',
            name='part_color',
            field=models.CharField(default='mono', max_length=25),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='streetfighterdrum',
            name='part_color',
            field=models.CharField(default='mono', max_length=25),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='streetfightertoner',
            name='part_color',
            field=models.CharField(default='mono', max_length=25),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='proposal',
            name='default_toner_type',
            field=models.CharField(choices=[('OEM', 'OEM'), ('REMAN', 'Reman'), ('OEM_SMP', 'OEM SMP')], default='OEM', max_length=10),
        ),
    ]
