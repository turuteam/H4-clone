# Generated by Django 2.2.1 on 2019-06-20 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0045_proposalserviceitem_proposal_purchase_item'),
    ]

    operations = [
        migrations.AlterField(
            model_name='printercost',
            name='msrp_cost',
            field=models.DecimalField(decimal_places=4, max_digits=9, null=True),
        ),
        migrations.AlterField(
            model_name='printercost',
            name='out_cost',
            field=models.DecimalField(decimal_places=4, max_digits=9, null=True),
        ),
    ]
