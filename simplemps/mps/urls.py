from django.urls import include, path, re_path
from django.views.generic.base import RedirectView

from . import views
from .controllers import imports, model_update
from .controllers import dca, print_fleet_
from .self_service import get_self_service_landing, get_self_service_equipment, get_self_service_selection, get_self_service_review, get_self_service_selection_landing

app_name = 'mps'

PROPOSAL_URLS = [
    path('createNewProposalSelfService/', model_update.create_proposal_external_source),
    path('updateProposalUserInfoSelfService/', model_update.update_proposal_user_info_self_service),
    path('createNewProposal/', model_update.create_proposal),
    path('selectClient/', RedirectView.as_view(url='/openProposals')),
    path('selectClient/<int:client_id>/edit', model_update.update_client),
    path('selectClient/<int:proposal_id>/', views.select_client),
    path('selectClient/saveProposal/', model_update.update_proposal_client_page),
    path('saveNewClient/', model_update.create_client),
    path('saveProposedCPP/', views.save_proposed_cpp),
    path('details/', RedirectView.as_view(url='/openProposals')),
    path('details/<int:proposal_id>/', views.proposal_details),
    path('getCompanyForExternalSource/', model_update.get_company_info_external_source),
    path('getManagementSettings/<int:assumptions_id>/', views.get_management_settings),
    path('getProposalSettings/<int:proposal_id>/', views.get_proposal_settings),
    path('getProposalItems/<int:proposal_id>/', views.get_proposal_items),
    path('getProposalPurchaseItem/<int:proposal_purchase_item_id>/', views.get_proposal_purchase_item),
    path('details/saveProposal/', model_update.update_proposal_details_page),
    path('pricing/', RedirectView.as_view(url='/openProposals')),
    path('pricing/<int:proposal_id>/update_tco_calculations', model_update.update_tco_calculations),
    path('pricing/<int:proposal_id>/', views.proposal_pricing, name="proposal_pricing"),
    path('TCO/<int:proposal_id>/', views.proposal_tco, name="proposal_tco"),
    path('TCO/<int:proposal_id>/sync', views.proposal_tco_sync, name="proposal_tco_sync"),
    path('getTCO/<int:proposal_id>/', views.proposal_get_tco, name="proposal_get_tco"),
    path('TCO/saveProposalTCO/', model_update.update_proposalTCO),
    path('TCO/<int:proposal_id>/updateTCODevice/', model_update.update_tco_device),
    path('getNetworkDeviceDetails/', views.get_network_device_details),
    path('getNonNetworkDeviceDetails/', views.get_non_network_device_details),
    path('getMakeDetails/', views.get_make_details),
    path('getPrinterDetails/', views.get_printer_details),
    path('getPrinterDetailsByMake/<int:make_id>/', views.get_printer_details_byMake),
    path('getUpdatedProposalServiceItems/<int:proposal_id>/', views.get_proposal_service_items_list),
    path('view/cpp/<int:proposal_id>/', views.view_proposal_cpp, name='view_proposal_cpp'),
    path('view/nc/<int:proposal_id>/', views.view_proposal_nc, name='view_proposal_nc'),
    path('view/blended/<int:proposal_id>/', views.view_proposal_blended, name='view_proposal_blended'),
    path('view/tiered/<int:proposal_id>/', views.view_proposal_tiered, name='view_proposal_tiered'),
    path('view/ppc/<int:proposal_id>/', views.view_proposal_ppc, name='view_proposal_ppc'),
    path('accept/<int:proposal_id>', views.accept_proposal, name='accept_proposal'),
    path('send/<int:proposal_id>', views.send_proposal, name='send_proposal'),
    path('send_to_me/<int:proposal_id>', views.send_proposal_to_me, name='send_proposal_to_me'),
    path('preview/', RedirectView.as_view(url='/openProposals')),
    path('preview/<int:proposal_id>/', views.proposal_preview),
    path('addNetworkDevice/<int:proposal_id>/', model_update.create_proposal_network_device),
    path('addTCODevice/<int:proposal_id>/', model_update.create_proposal_tco_device),
    path('removeNetworkDevice/<int:proposal_id>/', model_update.remove_proposal_network_device),
    path('removeTCODevice/<int:proposal_id>/', model_update.remove_proposal_tco_device),
    path('TCODeviceDetails/<int:proposal_id>/', views.tco_device_details),
    path('saveBlendedProposalData/<int:proposal_id>/', model_update.save_blended_proposal_data),
    path('saveTieredProposalData/<int:proposal_id>/', model_update.save_tiered_proposal_data),
    path('saveMarginAlert/<int:proposal_id>/', model_update.save_margin_alert),
    path('pricing/<int:proposal_id>/update_tier/', model_update.update_proposal_item_tier),
    path('updateProposalServiceItem/', model_update.update_proposal_service_item),
    path('requestStreetFighterPricing/', views.request_street_fighter_pricing),
    path('acceptStreetFighterPricing/', views.accept_street_fighter_pricing),
    path('getManagementAssumptions/', views.get_management_assumptions),
    # csv export 
    # path('consolidate-specifications/', views.consolidate_model_specifications),
    # path('build-specs/',views.build_model_specifications)
]

CONTRACT_URLS = [
    path('view/<int:proposal_id>/', views.view_contract, name='view_contract'),
]

urlpatterns = [
    #login
    path('accounts/', include('django.contrib.auth.urls')),
    ###
    path('imports/', views.import_home),
    path('', views.repDashboard),
    path('imports/parse-printer-data/', imports.import_printers),
    path('imports/import-makes/', imports.import_makes),
    path('imports/import-printer-costs/', imports.import_printer_costs),
    path('imports/import-accessories/', imports.import_accessories),
    path('imports/import-products/', imports.import_products),
    path('imports/import-toner-data/', imports.import_toners),
    path('imports/import-drums/', imports.import_drums),
    path('imports/import-developers/', imports.import_developers),
    path('imports/import-service/', imports.import_service),
    path('imports/import-device-makeup/', imports.import_device_makeup),
    path('imports/import-dca-post/<int:proposal_id>', imports.import_dca_post),
    path('imports/create-new-company/', model_update.create_company),
    path('imports/import-hw-data/', imports.import_hw_data),
    path('imports/import-supplies-data/', imports.import_supplies_data),
    path('summary/', views.summary_page),
    path('alerts/', views.alerts),
    path('alerts/getStreetFighterItems/<int:alert_id>/', views.get_street_fighter_items),
    path('alerts/saveStreetFighterCosts/<int:alert_id>/', views.save_street_fighter_costs),
    path('alerts/acceptStreetFighterPricing/<int:proposal_id>/', views.accept_street_fighter_pricing),
    path('alerts/declineStreetFighterPricing/<int:proposal_id>/', views.decline_street_fighter_pricing),

    #reps
    path('repDashboard/', views.repDashboard),
    path('proposal/', include(PROPOSAL_URLS)),
    path('contract/', include(CONTRACT_URLS)),
    path('openProposals/', views.openProposals),
    path('sentProposals/', views.sentProposals),
    path('contracts/', views.contracts),
    path('SalesRep/', views.SalesRep),
    path('settings/', views.account_settings, name='account_settings'),
    path('openProposals/proposals/', views.openProposalTableInfo),
    #anything that wants to delete a proposal can use this path below
    re_path(r'\w*/removeProposal/', model_update.delete_proposal),

    #manager
    path('manageReps/', views.manageReps),
    path('manageAssumptions/', views.manageAssumptions),
    path('manageAssumptions/update', model_update.update_assumption),
    path('manageReps/update', model_update.update_rep),
    path('manageReps/delete', model_update.delete_rep),

    #punchout  (gel 04/24/2020)
    path('punchout/', views.punchout),
    path('punchout/createNewProposal/', model_update.punchout_create_proposal),
    path('punchout/saveNewClient/', model_update.punchout_create_client),
    path('punchout/selectClient/<int:proposal_id>/', views.punchout_select_client),

    #my account
    path('myAccount/', views.my_account_equipment),
    path('myAccount/equipment/', views.my_account_equipment),
    path('myAccount/supplies/', views.my_account_supplies),
    path('myAccount/service/', views.my_account_service),
    path('myAccount/tcv/', views.my_account_tcv),
    path('myAccount/tcv/<int:proposal_id>', views.view_tcv, name="view_tcv"),
    path('myAccount/tcv/<int:proposal_id>/download', views.download_tcv, name="download_tcv"),

    # API
    path('api/', include('api.urls')),
    # leasing
    path('leasing-data/', model_update.get_leasing_data),
    path('calculate-lease-payment/', model_update.calculate_lease_payment),

    #dca import
    path('dca/accounts/<int:proposal_id>', dca.accounts),
    path('dca/device-info/<int:account_id>', dca.device_info),
    path('dca/device-data/<int:account_id>', dca.device_data),

    # print_fleet
    path('print_fleet/groups/<int:proposal_id>', print_fleet_.groups),
    path('print_fleet/group/<str:group_id>', print_fleet_.group),
    path('print_fleet/devices/<str:group_id>', print_fleet_.devices),
    path('print_fleet/device_data/<str:group_id>', print_fleet_.device_data),

    # Self-Service Portal
    path('self-service/<str:client_self_service_key>/', get_self_service_landing),
    path('self-service/<str:client_self_service_key>/<str:proposal_id>/equipment', get_self_service_equipment),
    path('self-service/<str:client_self_service_key>/<str:proposal_id>/selection', get_self_service_selection),
    path('self-service/<str:client_self_service_key>/<str:proposal_id>/review', get_self_service_review),

    path('self-service/<str:client_self_service_key>/self-service-selection', get_self_service_selection_landing),
]
