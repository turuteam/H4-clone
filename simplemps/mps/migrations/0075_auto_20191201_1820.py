# Generated by Django 2.2.1 on 2019-12-01 18:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0074_merge_20191108_1751'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountsetting',
            name='co_branding_logo',
            field=models.ImageField(default='logos/logo1.png', upload_to='logos/'),
        ),
        migrations.AlterField(
            model_name='accountsetting',
            name='logo',
            field=models.ImageField(default='logos/logo1.png', upload_to='logos/'),
        ),
    ]