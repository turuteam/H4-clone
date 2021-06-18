from rest_framework import serializers

from mps.models import (
    Accessory,
    ManagerAlert,
    PageCost,
    PrinterCost,
    Proposal,
    ProposalPurchaseItem,
    ProposalServiceItem,
    Toner,
    Client
)
from mps.views import get_scaled_toner_costs


class PrinterCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrinterCost
        fields = [
            'id',
            'product_id',
            'long_model',
            'printer',
            'company',
            'out_cost',
            'msrp_cost',
            'care_pack_cost',
        ]


class AccessorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Accessory
        fields = '__all__'


class ManagerAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagerAlert
        fields = '__all__'


class PageCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageCost
        fields = '__all__'


class ProposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proposal
        fields = '__all__'


class ProposalPurchaseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalPurchaseItem
        fields = '__all__'


class ProposalServiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalServiceItem
        fields = '__all__'

    # TODO Finish this. Running into decimal/float issues.
    # Punting for now, saving values directly from front end. 🤮
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # management_assumptions = instance.proposal.management_assumptions
        # toner_costs = get_scaled_toner_costs(
        #     management_assumptions,
        #     instance.proposal,
        #     instance.printer,
        #     instance.proposal.sales_rep.company,
        # )
        #
        # instance.set_recommended_mono_toner_price(toner_costs['scaled_mono_cost'])
        # instance.set_recommended_color_toner_price(toner_costs['scaled_color_cost'])
        # instance.set_service_price(toner_costs['scaled_service_cost'])
        # instance.set_recommended_mono_cpp()
        # instance.set_recommended_color_cpp()
        # instance.set_tiers(management_assumptions)

        instance.save()

        return instance

class TonerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Toner
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Client
        fields = '__all__'