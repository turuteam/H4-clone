from rest_framework import generics, viewsets

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
from .serializers import (
    AccessorySerializer,
    ManagerAlertSerializer,
    PageCostSerializer,
    PrinterCostSerializer,
    ProposalPurchaseItemSerializer,
    ProposalSerializer,
    ProposalServiceItemSerializer,
    TonerSerializer,
    ClientSerializer
)


class AccessoryViewSet(viewsets.ModelViewSet):
    queryset = Accessory.objects.all()
    serializer_class = AccessorySerializer


class ManagerAlertViewSet(viewsets.ModelViewSet):
    queryset = ManagerAlert.objects.all()
    serializer_class = ManagerAlertSerializer

    def get_queryset(self):
        queryset = ManagerAlert.objects.all()
        proposal_id = self.request.query_params.get('proposal_id', None)
        alert_type = self.request.query_params.get('alert_type', None)

        if proposal_id is not None:
            queryset = queryset.filter(proposal_id=proposal_id)

        if alert_type is not None:
            queryset = queryset.filter(alert_type=alert_type)

        return queryset


class PageCostViewSet(viewsets.ModelViewSet):
    queryset = PageCost.objects.all()
    serializer_class = PageCostSerializer


class PrinterCostAPIView(generics.RetrieveUpdateAPIView):
    queryset = PrinterCost.objects.all()
    serializer_class = PrinterCostSerializer


class ProposalViewSet(viewsets.ModelViewSet):
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer


class ProposalPurchaseItemViewSet(viewsets.ModelViewSet):
    queryset = ProposalPurchaseItem.objects.all()
    serializer_class = ProposalPurchaseItemSerializer


class ProposalServiceItemViewSet(viewsets.ModelViewSet):
    queryset = ProposalServiceItem.objects.all()
    serializer_class = ProposalServiceItemSerializer


class TonerViewSet(viewsets.ModelViewSet):
    queryset = Toner.objects.all()
    serializer_class = TonerSerializer

class ClientViewSet(viewsets.ModelViewSet): 
    queryset = Client.objects.all()
    serializer_class = ClientSerializer