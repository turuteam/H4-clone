# Generated by Django 2.2.1 on 2019-05-30 18:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mps', '0044_auto_20190528_2008'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposalserviceitem',
            name='proposal_purchase_item',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mps.ProposalPurchaseItem'),
        ),
    ]