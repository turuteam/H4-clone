from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .self_service_api import getCostPerCartridge, create_proposal_network_device_self_service

from .views import (
    AccessoryViewSet,
    ManagerAlertViewSet,
    PrinterCostAPIView,
    PageCostViewSet,
    ProposalPurchaseItemViewSet,
    ProposalServiceItemViewSet,
    ProposalViewSet,
    TonerViewSet,
    ClientViewSet
)


router = DefaultRouter()
router.register(r'accessories', AccessoryViewSet)
router.register(r'manager-alerts', ManagerAlertViewSet)
router.register(r'page-costs', PageCostViewSet)
router.register(r'proposals', ProposalViewSet)
router.register(r'proposal-purchase-items', ProposalPurchaseItemViewSet)
router.register(r'proposal-service-items', ProposalServiceItemViewSet)
router.register(r'toners', TonerViewSet)
router.register(r'client-info', ClientViewSet)

urlpatterns = [
    path('printer-cost/<int:pk>/', PrinterCostAPIView.as_view()),
    path('self-service-ppc/<int:proposal_id>/<int:printer_id>/', getCostPerCartridge),
    path('self-service/addNetworkDeviceSelfService/<int:proposal_id>/', create_proposal_network_device_self_service),
]

urlpatterns += router.urls
