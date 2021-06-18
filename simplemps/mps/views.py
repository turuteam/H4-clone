import csv
from collections import defaultdict
import fiscalyear
import json
import math
import os

from fiscalyear import *
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError
from django.db.models import Max, Sum, Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.template.defaulttags import register
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils.safestring import SafeString
from django.views.decorators.csrf import csrf_exempt
from .controllers.model_update import create_tier_values
from .controllers.printer_part import get_device_part
from .controllers.street_fighter import (create_street_fighter_items,
                                         delete_existing_sf_items,
                                         get_sf_item_info_list, update_street_fighter_costs)
from .controllers.utils import convert_class_to_primitives, get_flat_rate
from .models import *

from . forms import AccountSettingForm, SignatureForm
from jsignature.utils import draw_signature
from shutil import *
from django.conf import settings


#begin get management assumptions (GEL 2019-08-31)
@login_required
def get_management_settings(request, assumptions_id):
    mgmt_settings = ManagementAssumption.objects.get(id=assumptions_id)
    context_raw = {
        'allow_cartridge_pricing': mgmt_settings.allow_cartridge_pricing,
        'cpc_toner_only': mgmt_settings.cpc_toner_only,
        'allow_leasing': mgmt_settings.allow_leasing,
        'allow_rental': mgmt_settings.allow_rental,
        'allow_reman': mgmt_settings.allow_reman,
        'allow_tiered': mgmt_settings.allow_tiered,
        'allow_tco': mgmt_settings.allow_tco,
        'allow_flat_rate': mgmt_settings.allow_flat_rate,
        'target_margin_equipment': float(mgmt_settings.target_margin_equipment)
    }
    #print (json.dumps(context_raw))
    return JsonResponse(json.dumps(context_raw), safe=False)
#end management assuptions insert

#begin get proposal settings (GEL 2019-12-04)

# @login_required
def get_proposal_settings(request, proposal_id):
    proposal_settings = Proposal.objects.get(id=proposal_id)
    client_settings = Client.objects.get(id=proposal_settings.client_id)
    context_raw = {
        'status': proposal_settings.status,
        'term': proposal_settings.term,
        'contract_service_type': proposal_settings.contract_service_type,
        'default_toner_type': proposal_settings.default_toner_type,
        'auto_pop_base': proposal_settings.auto_populate_base_info,
        'company_id': client_settings.rep_company_id,
        'proposal_type': proposal_settings.proposal_type
    }
    return JsonResponse(json.dumps(context_raw), safe=False)
#end proposal settings insert

#begin get proposal items count (GEL 2019-10-11)
@login_required
def get_proposal_items(request, proposal_id):
    service_item_count = ProposalServiceItem.objects.filter(proposal_id=proposal_id).count()
    context_raw = {
        'service_item_count': service_item_count
    }
    return JsonResponse(json.dumps(context_raw), safe=False)
#end insert

@login_required
@require_http_methods(['GET'])
def openProposalTableInfo(request):
    proposals = getOpenProposals(request)
    return HttpResponse(json.dumps(proposals))

@login_required
def repDashboard(request):
    #this method will have more dictionaries once we fill out the other
        #pages with their functionality

    dashboard_prop_prog = getOpenProposals(request, ['in-progress'])
    #sent_proposals = getOpenProposals(request, ['proposal_sent', 'proposal_declined', 'proposal_accepted'])

    sent_proposals = getSentProposals(request, ['proposal_sent'])
    #sent_proposals = dashboard_prop_prog

    open_contracts = getAcceptedProposals(request, ['proposal_accepted'])
    #open_contracts = dashboard_prop_prog

    # need self service key to get started, use the test id: Testing.
    # company = Company.objects.get(pk=9)
    
    rep_company_id = request.user.mps_user.company_id
    company = Company.objects.get(pk=rep_company_id)
    self_service_key = company.self_service_key

    status_list = ['in-progress', 'proposal_sent', 'proposal_accepted']
    status_list_verbose = dict(zip(status_list, ['in-progress', 'sent', 'accepted']))

    return render(request, 'rep/repDashboard.html', {
        'dashboard_prop_prog': dashboard_prop_prog,
        'sent_proposals' : sent_proposals,
        'open_contracts': open_contracts,
        'status_list': status_list,
        'status_list_verbose': status_list_verbose,
        'self_service_key': self_service_key
    })

def as_currency(amount):
    if amount >= 0:
        return '${:,.2f}'.format(amount)
    else:
        return '-${:,.2f}'.format(-amount)


#gets all of the information needed for the open proposals table in either
    # open proposal page, or the rep dashboard. We need to return the id
    # because it will be used for the editing, deleting and other methods
    # ---returns---
    # - client
    # - date_edited
    # - status
    # - est_value
    # - proposal_id


def get_dashboard_items(proposal):
    item = {}
    client = proposal.client
    sales_rep = proposal.sales_rep.user

    item['client'] = getattr(client, "organization_name", "N/A")
    date_obj = proposal.create_date  # TODO make this actual date last edited
    date_edited_str = '%s/%s/%s' % (date_obj.month, date_obj.day, date_obj.year)
    item['date_edited'] = date_edited_str
    item['date_sent'] = None  # TODO: add date sent date
    item['status'] = proposal.status
    item['est_value'] = as_currency(0)  # TODO: add estimated value
    item['proposal_id'] = proposal.id
    item['estimated_value'] = estimate_value(proposal)

    item['sales_rep_name'] = '{0} {1}'.format(sales_rep.first_name, sales_rep.last_name)
    return item


@login_required
def getOpenProposals(request, status=['in-progress']):
    dashboard_prop_prog = []
    #match proposals on the salesrep, and make sure they aren't deleted
    this_rep = request.user.mps_user
    for p in Proposal.objects.filter(sales_rep=this_rep, is_deleted=False):
        item = get_dashboard_items(p)
        if item != None and item['status'] in status:
            dashboard_prop_prog.append(item)
        else:
            pass
    return dashboard_prop_prog

#gets all of the information needed for the sent proposals table in either
    # open proposal page, or the rep dashboard. We need to return the id
    # because it will be used for the editing, deleting and other methods
    # ---returns---
    # - client
    # - date_edited
    # - status
    # - est_value
    # - proposal_id
@login_required
def getSentProposals(request, status=['proposal_sent']):
    def get_dashboard_items(proposal):
        item = {}
        client = proposal.client

        item['client'] = getattr(client, "organization_name", "N/A")
        date_obj = proposal.create_date #TODO make this actual date last edited
        date_edited_str = '%s/%s/%s'%(date_obj.month, date_obj.day, date_obj.year)
        item['date_edited'] = date_edited_str
        item['date_sent'] = date_edited_str #TODO: add date sent date to database and
        item['status'] = proposal.status
        item['est_value'] = as_currency(0) #TODO: add estimated value
        item['proposal_id'] = proposal.id
        item['estimated_value'] = estimate_value(proposal)
        return item

    dashboard_prop_prog = []
    #match proposals on the salesrep, and make sure they aren't deleted
    this_rep = request.user.mps_user
    for p in Proposal.objects.filter(sales_rep=this_rep, is_deleted=False):
        item = get_dashboard_items(p)
        if item != None and item['status'] in status:
            dashboard_prop_prog.append(item)
        else:
            pass
    return dashboard_prop_prog

#gets accepted-proposal information for the open contracts table in either
    # open proposal page, or the rep dashboard. We need to return the id
    # because it will be used for the editing, deleting and other methods
@login_required
def getAcceptedProposals(request, status=['proposal_accepted']):
    def get_dashboard_items(proposal):
        item = {}
        client = proposal.client

        item['client'] = getattr(client, "organization_name", "N/A")
        date_obj = proposal.create_date #TODO make this actual date last edited
        date_edited_str = '%s/%s/%s'%(date_obj.month, date_obj.day, date_obj.year)
        item['date_edited'] = date_edited_str
        item['date_sent'] = date_edited_str #TODO: add date sent date to database and
        item['status'] = proposal.status
        item['est_value'] = as_currency(0) #TODO: add estimated value
        item['proposal_id'] = proposal.id
        item['estimated_value'] = estimate_value(proposal)
        return item

    dashboard_prop_prog = []
    #match proposals on the salesrep, and make sure they aren't deleted
    this_rep = request.user.mps_user
    for p in Proposal.objects.filter(sales_rep=this_rep, is_deleted=False):
        item = get_dashboard_items(p)
        if item != None and item['status'] in status:
            dashboard_prop_prog.append(item)
        else:
            pass
    return dashboard_prop_prog

#TODO: implement estimated value of contract
def estimate_value(proposal):
    print("estimate value of proposal not implemented yet")
    return None

@login_required
def contracts(request):
#    return render(request, 'rep/contracts.html')
    dashboard_prop_prog = getAcceptedProposals(request, ['proposal_accepted'])

    return render(request, 'rep/contracts.html', {'dashboard_prop_prog': dashboard_prop_prog})

#   This displays a static page with dummy info
#@login_required
#def sentProposals(request):
#    return render(request, 'rep/sentProposals.html')
#


@login_required
def sentProposals(request):
    dashboard_prop_prog = getSentProposals(request, ['proposal_sent'])

    return render(request, 'rep/sentProposals.html', {'dashboard_prop_prog': dashboard_prop_prog})


@login_required
def openProposals(request):
    dashboard_prop_prog = getOpenProposals(request)

    return render(request, 'rep/openProposals.html', {'dashboard_prop_prog': dashboard_prop_prog})


@login_required
def getOpenProposalsManager(sales_rep, status=['in-progress']):
    dashboard_prop_prog = []
    # match proposals on the salesrep, and make sure they aren't deleted
    for p in Proposal.objects.filter(sales_rep=sales_rep, is_deleted=False):
        item = get_dashboard_items(p)
        if item != None and item['status'] in status:
            dashboard_prop_prog.append(item)
        else:
            pass
    return dashboard_prop_prog


@login_required
def SalesRep(request):
    user = request.user

    if user.groups.filter(name='Admin').exists() or user.groups.filter(name='Manager').exists():
        print('User is Admin or Manager')
        dashboard_prop_prog = []

        for sales_rep in MPS_User.objects.filter(~Q(user_id=user.id), company=request.user.mps_user.company):
            dashboard_prop_prog.extend(getOpenProposalsManager(sales_rep))

    else:
        dashboard_prop_prog = getOpenProposals(request.user.mps_user)

    return render(request, 'rep/SalesRep.html', {'dashboard_prop_prog': dashboard_prop_prog})


@login_required
def manageAssumptions(request):
    try:
        context = {
            'assumptions': ManagementAssumption.objects.get(company=request.user.mps_user.company),
            'commission_choices': ManagementAssumption.COMMISSION_CHOICES,
            'non_net_choices': ManagementAssumption.NON_NETWORK_COMMISSION_CHOICES,
            'eq_commission_choices': ManagementAssumption.EQ_COMMISSION_CHOICES,
            'cart_range': range(1, 11), # 1-10
            'maint_range': range(1, 5),    # 1-4
            'perc_range': range(5, 95, 5),  #5, 10, 15, ..., 90
            'manufacturers': MANUFACTURER_CHOICES
        }

        return render(request, 'manager/manageAssumptions.html', context)

    except ManagementAssumption.DoesNotExist:
        return JsonResponse({'status':'Fail', 'msg': 'Could not access management assumptions'})


@login_required    #punchout (gel 04/24/2020)
def punchout(request):
    try:
        context = {
            'assumptions': ManagementAssumption.objects.get(company=request.user.mps_user.company),
            'commission_choices': ManagementAssumption.COMMISSION_CHOICES,
            'non_net_choices': ManagementAssumption.NON_NETWORK_COMMISSION_CHOICES,
            'eq_commission_choices': ManagementAssumption.EQ_COMMISSION_CHOICES,
            'cart_range': range(1, 11), # 1-10
            'maint_range': range(1, 5),    # 1-4
            'perc_range': range(5, 95, 5),  #5, 10, 15, ..., 90
            'manufacturers': MANUFACTURER_CHOICES
        }

        return render(request, 'manager/punchout/punchout.html', context)

    except ManagementAssumption.DoesNotExist:
        return JsonResponse({'status':'Fail', 'msg': 'Could not access management assumptions'})
# select_client
@login_required
def punchout_select_client(request, proposal_id):
    proposal = Proposal.objects.get(id=proposal_id)

    all_clients = {}
    for c in Client.objects.filter(rep_company=request.user.mps_user.company):
        all_clients[c.id] = model_to_dict(c)

    context = {
        'proposal_client': proposal.client,
        'all_clients': Client.objects.filter(rep_company=request.user.mps_user.company),
        'all_clients_obj': json.dumps(all_clients),
        'proposal_id': proposal_id,
        'contract_service_level': proposal.contract_service_level
    }

    return render(request, 'manager/punchout/selectClient.html', context)

@login_required
def manageReps(request):
    if request.method == 'GET':
        try:
            #ID increment problem
            users = MPS_User.objects.all()
            rep_proposals = []
            pending_proposals = {}
            sent_proposals = {}
            unsigned_contracts = {}
            closed_contracts = {}
            mps_sales = {}
            equipment_sales = {}

            for user in users:
                equipment_sales[user] = 0
                mps_sales[user] = 0
                pending_proposals[user] = 0
                sent_proposals[user] = 0
                unsigned_contracts[user] = 0
                closed_contracts[user] = 0

                for proposal in Proposal.objects.filter(sales_rep=user):
                    equipment_sales[user] += 0 #TODO: need to calculate estimated value on the fly, model should do this for us
                    mps_sales[user] += 111
                    if proposal.is_approved:
                        sent_proposals[user] += 1
                    if not proposal.is_approved:
                        pending_proposals[user] += 1
                    if proposal.is_deleted:
                        closed_contracts[user] += 1

            args = {
                'proposals':rep_proposals,
                'users':users,
                'pendingProposalMap':pending_proposals,
                'sentProposalMap':sent_proposals,
                'unsignedContractMap':unsigned_contracts,
                'closedContractMap':closed_contracts,
                'mpsSaleMap':mps_sales,
                'equipmentSaleMap':equipment_sales,
            }

            return render(request, 'manager/manageReps.html', args)

        except Proposal.DoesNotExist:
            return JsonResponse({'status':'Fail', 'msg': 'Object does not exist'})

    else:
        return JsonResponse({'status':'Fail', 'msg':'fail'})

@register.filter
def get_value(dictionary, key):
    return dictionary.get(key)

@login_required
def alerts(request):
    margin_alerts = []
    for alert in ManagerAlert.objects.filter(company=request.user.mps_user.company, alert_type=ManagerAlert.MARGIN):
        proposal = alert.proposal
        service_items = ProposalServiceItem.objects.filter(proposal=proposal)

        if alert.was_approved == None:
            margin_alerts.append({
                'id': alert.id,
                'proposal_id': proposal.id,
                'create_date': alert.create_date,
                'rep': request.user.username,
                'rep_id': request.user.id,
                'client': proposal.client.organization_name,
                'num_devices': service_items.aggregate(num=Sum('number_printers_serviced'))['num'],
            })

    sf_alerts = []
    for alert in ManagerAlert.objects.filter(company=request.user.mps_user.company, alert_type=ManagerAlert.STREET_FIGHTER):
        proposal = alert.proposal
        service_items = ProposalServiceItem.objects.filter(proposal=proposal)

        if proposal.street_fighter_status == Proposal.PENDING:
            sf_alerts.append({
                'id': alert.id,
                'proposal_id': proposal.id,
                'create_date': alert.create_date,
                'rep': request.user.username,
                'client': proposal.client.organization_name,
                'num_devices': service_items.aggregate(num=Sum('number_printers_serviced'))['num'],
            })

    context = {
        'margin_alerts': margin_alerts,
        'sf_alerts': sf_alerts
    }
    return render(request, 'rep/alerts.html', context)

# @login_required
def get_printer_details(request):
    printers = list(Printer.objects.filter().values_list('id', 'short_model').order_by('short_model'))
    return JsonResponse(json.dumps({'printers': printers}), safe=False)

#Return list of printers made by a specific manufacturer
# @login_required
def get_printer_details_byMake(request, make_id):
    printers = list(Printer.objects.filter(make_id=make_id).values_list('id', 'short_model').order_by('short_model'))
    return JsonResponse(json.dumps({'printers': printers}), safe=False)

#Return a list of manufacturer names/ids for selection
# @login_required
def get_make_details(request):
    makes = list(Make.objects.filter().values_list('id', 'name').order_by('name'))
    return JsonResponse(json.dumps({'makes': makes}), safe=False)

@login_required
def select_client(request, proposal_id):
    proposal = Proposal.objects.get(id=proposal_id)

    all_clients = {}
    for c in Client.objects.filter(rep_company=request.user.mps_user.company):
        all_clients[c.id] = model_to_dict(c)

    context = {
        'proposal_client': proposal.client,
        'all_clients': Client.objects.filter(rep_company=request.user.mps_user.company),
        'all_clients_obj': json.dumps(all_clients),
        'proposal_id': proposal_id,
        'contract_service_level': proposal.contract_service_level
    }

    return render(request, 'rep/newProposal/selectClient.html', context)

@login_required
def proposal_details(request, proposal_id):
    try:
        proposal = Proposal.objects.get(pk=proposal_id)

        sales_rep = MPS_User.objects.get(pk=proposal.sales_rep.id)
        company = Company.objects.get(pk=sales_rep.company.id)

        MOD_MANUFACTURER_CHOICES =  [i for i in MANUFACTURER_CHOICES]
        context = {
            'proposal_id': proposal_id,
            'proposal_details': json.dumps({
                'proposal_id': proposal_id,
                'term': proposal.term if proposal.term is not None else -1,
                'contractType': proposal.contract_service_type if proposal.contract_service_type is not None else -1,
                'manufacturer': proposal.default_toner_type if proposal.default_toner_type is not None else -1,
                'propOutsideLoc': float(proposal.proportion_fleet_offsite) if proposal.proportion_fleet_offsite is not None else -1,
                'zone_01': float(proposal.zone_01) if proposal.zone_01 is not None else -1,
                'zone_02': float(proposal.zone_02) if proposal.zone_02 is not None else -1,
                'zone_03': float(proposal.zone_03) if proposal.zone_03 is not None else -1,
                'auto_pop_base': proposal.auto_populate_base_info if proposal.auto_populate_base_info is not None else -1,
                'serviceLevel': proposal.contract_service_level.name if proposal.contract_service_level is not None else -1,
                'assumptions_id': proposal.management_assumptions_id
            }),
            'company_id': company.id,
            'manufacturers': MOD_MANUFACTURER_CHOICES,
            'toner_type': proposal.default_toner_type,
            'client': proposal.client.organization_name,
            'contract_service_level': proposal.contract_service_level
        }
        return render(request, 'rep/newProposal/details.html', context)
    except Proposal.DoesNotExist:
        #proposal did not exist, return to open proposals
        return redirect('/openProposals/')

# Retrieve info from ProposalPurchaseItems  (GEL 2019-11-20)
# @login_required
def get_proposal_purchase_item(request, proposal_purchase_item_id):
    purchase_item = ProposalPurchaseItem.objects.get(id=proposal_purchase_item_id)
    context_raw = {
        'buy_or_lease': purchase_item.buy_or_lease,
        'proposed_cost': float(purchase_item.proposed_cost)
    }
    return JsonResponse(json.dumps(context_raw), safe=False)

@login_required
def proposal_pricing(request, proposal_id):
    proposal = Proposal.objects.get(id=proposal_id)
    assumption = proposal.management_assumptions
    proposal_managementassumptions = {
        'proposal_id': proposal_id,
        'assumption_id': assumption.id,
        # rem -1 and  - ((proposal.term / 12) / 100)
        'target_margin_toner': float(assumption.target_margin_toner),
        'effective_mono_yield': float(assumption.effective_mono_yield),
        'effective_color_yield': float(assumption.effective_color_yield),
        'reman_rebate': float(assumption.reman_rebate),
        'oem_smp_rebate': float(assumption.oem_smp_rebate),
        'oem_rebate': float(assumption.oem_rebate),
        'toner_shipping_price': float(assumption.toner_shipping_price),
        'distro_markup': float(assumption.distro_markup),
        'supplies_only': float(assumption.supplies_only),
        'cpc_toner_only': assumption.cpc_toner_only,
        'annual_mono_cartridges': int(assumption.annual_mono_cartridges),
        'maintenance_kit_replaced_years': int(assumption.maintenance_kit_replaced_years),
        'percentage_color': float(assumption.percentage_color),
        'non_network_margin': float(assumption.non_network_margin),
        'commission_type': assumption.commission_type,
        'percent_margin_flat_rate': float(assumption.percent_margin_flat_rate),
        'percentage_revenue_flat_rate':float(assumption.percentage_revenue_flat_rate),
        'margin_rate_printers': float(assumption.margin_rate_printers),
        'margin_rate_copiers': float(assumption.margin_rate_copiers),
        'revenue_rate_printers': float(assumption.revenue_rate_printers),
        'revenue_rate_copiers': float(assumption.revenue_rate_copiers),
        'use_non_network_margin': assumption.pay_non_network_commission,
        # remove -1 and - ((proposal.term / 12) / 100)
        'target_margin_service': float(assumption.target_margin_service),
        'gold_service': float(assumption.gold_service),
        'platinum_service': float(assumption.platinum_service),
        'service_only': float(assumption.service_only),
        'inflate_older_than': int(assumption.inflate_older_than),
        'old_inflate_percent': float(assumption.old_inflate_percent),
        'inflate_out_of_area': float(assumption.inflate_out_of_area),
        'tier2_inflate': float(assumption.tier2_inflate),
        'tier3_inflate': float(assumption.tier3_inflate),
        'equipment_inflate': float(assumption.equipment_inflate),
        'accessory_inflate': float(assumption.accessory_inflate),
        'eq_commission_type': assumption.eq_commission_type,
        'eq_percent_margin_flat_rate': float(assumption.eq_percent_margin_flat_rate),
        'eq_percentage_revenue_flat_rate':float(assumption.eq_percentage_revenue_flat_rate),
        'eq_margin_rate_printers': float(assumption.eq_margin_rate_printers),
        'eq_margin_rate_copiers': float(assumption.eq_margin_rate_copiers),
        'eq_revenue_rate_printers': float(assumption.eq_revenue_rate_printers),
        'eq_revenue_rate_copiers': float(assumption.eq_revenue_rate_copiers),
        'toner_after_reman': assumption.toner_after_reman,
        'toner_after_oem_smp': assumption.toner_after_oem_smp,
        'min_mono_margin': float(assumption.min_mono_margin),
        'min_color_margin': float(assumption.min_color_margin),
        'min_mono_on_color_margin': float(assumption.min_mono_on_color_margin),
        'change_device_price_base': assumption.change_device_price_base,
        'managed_cartridge_inflate': float(assumption.managed_cartridge_inflate),
        'exchange_entire_model': float(assumption.exchange_entire_model),
        'exchange_service_to_currency': float(assumption.exchange_service_to_currency),
        'term': proposal.term,
        'contract_service_type': proposal.contract_service_type,
        'contract_service_level_name': proposal.contract_service_level.name,
        'contract_service_response_time': proposal.contract_service_level.responseTime,
        # The proportion_fleet_offsite field is no longer used
        'proportion_fleet_offsite': float(proposal.proportion_fleet_offsite if proposal.proportion_fleet_offsite else 0),
        'zone_01': float(proposal.zone_01 if proposal.zone_01 else 0),
        'zone_02': float(proposal.zone_02 if proposal.zone_02 else 0),
        'zone_03': float(proposal.zone_03 if proposal.zone_03 else 0),
        # Automatically load base volumes (if they exist) 
        'auto_pop_base': proposal.auto_populate_base_info if proposal.auto_populate_base_info is not None else -1,
        # next 5 values added to support HP (GEL 2019-08-31)
        'allow_cartridge_pricing': assumption.allow_cartridge_pricing,
        'allow_leasing': assumption.allow_leasing,
        'allow_rental': assumption.allow_rental,
        'allow_reman': assumption.allow_reman,
        'allow_tiered': assumption.allow_tiered,
        # next value added to support Flat Rate tab (GEL 2020-03-17)
        'allow_flat_rate': assumption.allow_flat_rate,
        # next 6 values added to manage pricing dependong on proposed contract duration
        'allow_term_offsets': assumption.allow_term_offsets,
        'cost_offset_12month': float(assumption.cost_offset_12month),
        'cost_offset_24month': float(assumption.cost_offset_24month),
        'cost_offset_36month': float(assumption.cost_offset_36month),
        'cost_offset_48month': float(assumption.cost_offset_48month),
        'cost_offset_60month': float(assumption.cost_offset_60month),
        # next option controls display of TCO tab and so forth
        'allow_tco': assumption.allow_tco,
        'tier2_inflate': float(assumption.tier2_inflate),
        'tier3_inflate': float(assumption.tier3_inflate),
        'target_margin_equipment': float(assumption.target_margin_equipment)
    }

    proposal_service_items = json.dumps(prep_proposal_service_items_list(request, proposal))

    tiered_values = TieredValue.objects.filter(proposal=proposal)

    if tiered_values.count() == 0:
        tiered_values = create_tier_values(proposal)
    else:
        tiered_values = tiered_values.first()

    if proposal.street_fighter_status == Proposal.APPROVED:
        street_fighter = "true"
    else:
        street_fighter = "false"

    proposal_purchase_items_queryset = ProposalPurchaseItem.objects.filter(proposal=proposal).values()
    proposal_purchase_items_list = []
    if proposal_purchase_items_queryset.count() > 0:
        proposal_purchase_items_list = list(map(lambda x: convert_class_to_primitives(x), proposal_purchase_items_queryset))
    
    context = {
        'proposal_json_string': json.dumps(proposal_managementassumptions),
        'proposal_service_items': proposal_service_items,
        'proposal_purchase_items': json.dumps(proposal_purchase_items_list),
        'proposal_id': proposal_id,
        'street_fighter': street_fighter,
        'tiered_values' : tiered_values,
        'client': proposal.client.organization_name
    }

    return render(request, 'rep/newProposal/pricing.html', context)

def prep_proposal_service_items_list(request, proposal):
    
    if(request.user.is_anonymous):
        # sales rep is mps user instance
        mps_user = MPS_User.objects.get(pk=proposal.sales_rep_id)
        user = User.objects.get(pk=mps_user.user_id) 
        this_rep = MPS_User.objects.get(user=user)
    else: 
        this_rep = request.user.mps_user
    # this_rep = request.user.mps_user
    
    proposal_service_items_queryset = ProposalServiceItem.objects.filter(proposal_id=proposal).values()

    proposal_service_items = []

    for psi_dict in proposal_service_items_queryset:
        item = convert_class_to_primitives(psi_dict)
        printer = Printer.objects.get(id=item['printer_id'])
        item['short_model'] = printer.short_model
        item['is_color_device'] = printer.is_color_device
        item['device_type'] = printer.device_type

        item['device_name'] = printer.short_model
        ps_item = ProposalServiceItem.objects.get(id=item['id'])
        item['device_count'] = ps_item.number_printers_serviced
        flat_rate = get_flat_rate(ps_item)

        if item['is_non_network']:
            item['monthly_cost'] = float(ps_item.non_network_cost)
        else:
            item['monthly_cost'] = flat_rate
            item['monthly_cost'] = '%.2f' % item['monthly_cost']

            item['mono_cpp'] = float(calculate_mono_cpp(item['short_model'], proposal.id, this_rep.company.id) * Decimal(item['mono_coverage']) / Decimal(0.05))
            if printer.is_color_device:
                item['color_cpp'] = float(calculate_color_cpp(item['short_model'], proposal.id, this_rep.company.id) * Decimal(item['color_coverage']) / Decimal(0.05))

        proposal_service_items.append(item)

    return proposal_service_items

def get_proposal_service_items_list(request, proposal_id):
    proposal = Proposal.objects.get(id=proposal_id)
    return HttpResponse(
        json.dumps(prep_proposal_service_items_list(request, proposal), indent=4),
        content_type="application/json",
    )

def proposal_tco_sync(request, proposal_id):
  return proposal_tco(request, proposal_id, True)

# new TCO module
@login_required
def proposal_tco(request, proposal_id, sync=False):
    proposal = Proposal.objects.get(id=proposal_id)
    proposal_tco, created = ProposalTCO.objects.get_or_create(
      proposal_id=proposal_id,
      contract_service_type = "total",
      total_supply_spend = 0,
      total_service_spend = 0,
      total_lease_spend = 0,
      est_transaction_overhead = 60,
      total_sales_orders = 0,
      total_service_orders = 0
    )

    if created or sync:
        ProposalTCOItem.objects.filter(proposalTCO=proposal_tco).delete()
        proposal_items = ProposalServiceItem.objects.filter(proposal=proposal).exclude(printer__isnull=True)

        tco_items = []
        for item in proposal_items:
          tco_item = ProposalTCOItem(
            proposalTCO = proposal_tco,
            printer = item.printer,
            proposalserviceitem_id = item.id,
            number_printers_serviced = item.number_printers_serviced,
            total_mono_pages = item.total_mono_pages,
            total_color_pages = item.total_color_pages,
            current_cpp_mono = float(item.rcmd_cpp_mono) * 1.10134,
            current_cpp_color = float(item.rcmd_cpp_color) * 1.10134,
            rcmd_cpp_mono = float(item.proposed_cpp_mono) * 1.10134,
            rcmd_cpp_color = float(item.proposed_cpp_color) * 1.10134,
            mono_toner_price = item.mono_toner_price,
            color_toner_price = item.color_toner_price,
            service_cost = item.service_cost,
            # base_volume_mono = item.base_volume_mono,
            # base_volume_color = item.base_volume_color,
            # base_rate_mono = float(item.base_rate_mono) * 1.10134,
            # base_rate_color = float(item.base_rate_mono) * 1.10134,
            base_volume_mono = 0,
            base_volume_color = 0,
            base_rate_mono = 0,
            base_rate_color = 0,
            printer_id = item.printer.id,
            proposalTCO_id = proposal_tco.id
          )
          tco_items.append(tco_item)

        ProposalTCOItem.objects.bulk_create(tco_items)

    client_data = Client.objects.get(id=proposal.client_id)

    proposal_tco_items = ProposalTCOItem.objects.filter(proposalTCO_id=proposal_tco.id)

    proposal_service_items = json.dumps(prep_proposal_service_items_list(request, proposal))

    proposal_purchase_items_queryset = ProposalPurchaseItem.objects.filter(proposal=proposal).values()
    proposal_purchase_items_list = []
    if proposal_purchase_items_queryset.count() > 0:
        proposal_purchase_items_list = list(map(lambda x: convert_class_to_primitives(x), proposal_purchase_items_queryset))

    assumption = proposal.management_assumptions

    proposal_managementassumptions = {
        'proposal_id': proposal_id,
        'assumption_id': assumption.id,
        # rem -1 and  - ((proposal.term / 12) / 100)
        'target_margin_toner': float(assumption.target_margin_toner),
        'effective_mono_yield': float(assumption.effective_mono_yield),
        'effective_color_yield': float(assumption.effective_color_yield),
        'reman_rebate': float(assumption.reman_rebate),
        'oem_smp_rebate': float(assumption.oem_smp_rebate),
        'oem_rebate': float(assumption.oem_rebate),
        'toner_shipping_price': float(assumption.toner_shipping_price),
        'distro_markup': float(assumption.distro_markup),
        'supplies_only': float(assumption.supplies_only),
        'cpc_toner_only': assumption.cpc_toner_only,
        'annual_mono_cartridges': int(assumption.annual_mono_cartridges),
        'maintenance_kit_replaced_years': int(assumption.maintenance_kit_replaced_years),
        'percentage_color': float(assumption.percentage_color),
        'non_network_margin': float(assumption.non_network_margin),
        'commission_type': assumption.commission_type,
        'percent_margin_flat_rate': float(assumption.percent_margin_flat_rate),
        'percentage_revenue_flat_rate':float(assumption.percentage_revenue_flat_rate),
        'margin_rate_printers': float(assumption.margin_rate_printers),
        'margin_rate_copiers': float(assumption.margin_rate_copiers),
        'revenue_rate_printers': float(assumption.revenue_rate_printers),
        'revenue_rate_copiers': float(assumption.revenue_rate_copiers),
        'use_non_network_margin': assumption.pay_non_network_commission,
        # remove -1 and - ((proposal.term / 12) / 100)
        'target_margin_service': float(assumption.target_margin_service),
        'gold_service': float(assumption.gold_service),
        'platinum_service': float(assumption.platinum_service),
        'service_only': float(assumption.service_only),
        'inflate_older_than': int(assumption.inflate_older_than),
        'old_inflate_percent': float(assumption.old_inflate_percent),
        'inflate_out_of_area': float(assumption.inflate_out_of_area),
        'tier2_inflate': float(assumption.tier2_inflate),
        'tier3_inflate': float(assumption.tier3_inflate),
        'equipment_inflate': float(assumption.equipment_inflate),
        'accessory_inflate': float(assumption.accessory_inflate),
        'eq_commission_type': assumption.eq_commission_type,
        'eq_percent_margin_flat_rate': float(assumption.eq_percent_margin_flat_rate),
        'eq_percentage_revenue_flat_rate':float(assumption.eq_percentage_revenue_flat_rate),
        'eq_margin_rate_printers': float(assumption.eq_margin_rate_printers),
        'eq_margin_rate_copiers': float(assumption.eq_margin_rate_copiers),
        'eq_revenue_rate_printers': float(assumption.eq_revenue_rate_printers),
        'eq_revenue_rate_copiers': float(assumption.eq_revenue_rate_copiers),
        'toner_after_reman': assumption.toner_after_reman,
        'toner_after_oem_smp': assumption.toner_after_oem_smp,
        'min_mono_margin': float(assumption.min_mono_margin),
        'min_color_margin': float(assumption.min_color_margin),
        'min_mono_on_color_margin': float(assumption.min_mono_on_color_margin),
        'change_device_price_base': assumption.change_device_price_base,
        'managed_cartridge_inflate': float(assumption.managed_cartridge_inflate),
        'exchange_entire_model': float(assumption.exchange_entire_model),
        'exchange_service_to_currency': float(assumption.exchange_service_to_currency),
        'term': proposal.term,
        'contract_service_type': proposal.contract_service_type,
        'contract_service_level_name': proposal.contract_service_level.name,
        'contract_service_response_time': proposal.contract_service_level.responseTime,
        # The proportion_fleet_offsite field is no longer used
        'proportion_fleet_offsite': float(proposal.proportion_fleet_offsite if proposal.proportion_fleet_offsite else 0),
        'zone_01': float(proposal.zone_01 if proposal.zone_01 else 0),
        'zone_02': float(proposal.zone_02 if proposal.zone_02 else 0),
        'zone_03': float(proposal.zone_03 if proposal.zone_03 else 0),
        # Automatically load base volumes (if they exist) 
        'auto_pop_base': proposal.auto_populate_base_info if proposal.auto_populate_base_info is not None else -1,
        # next 5 values added to support HP (GEL 2019-08-31)
        'allow_cartridge_pricing': assumption.allow_cartridge_pricing,
        'allow_leasing': assumption.allow_leasing,
        'allow_rental': assumption.allow_rental,
        'allow_reman': assumption.allow_reman,
        'allow_tiered': assumption.allow_tiered,
        # next value added to support Flat Rate tab (GEL 2020-03-17)
        'allow_flat_rate': assumption.allow_flat_rate,
        # next 6 values added to manage pricing dependong on proposed contract duration
        'allow_term_offsets': assumption.allow_term_offsets,
        'cost_offset_12month': float(assumption.cost_offset_12month),
        'cost_offset_24month': float(assumption.cost_offset_24month),
        'cost_offset_36month': float(assumption.cost_offset_36month),
        'cost_offset_48month': float(assumption.cost_offset_48month),
        'cost_offset_60month': float(assumption.cost_offset_60month),
        # next option controls display of TCO tab and so forth
        'allow_tco': assumption.allow_tco,
        'tier2_inflate': float(assumption.tier2_inflate),
        'tier3_inflate': float(assumption.tier3_inflate),
        'target_margin_equipment': float(assumption.target_margin_equipment)
    }

    context = {
        'proposal_json_string': SafeString(json.dumps(proposal_managementassumptions)),
        'proposal_service_items': SafeString(json.dumps(proposal_service_items)),
        'proposal_purchase_items': SafeString(json.dumps(proposal_purchase_items_list)),
        'proposalTCO_id': proposal_tco.id,
        'proposal_id': proposal_id,
        'client': client_data.organization_name,
        'mps_price': proposal.mps_price,
        'monthly_lease': proposal.monthly_lease,
        'proposal_term': proposal.term,
        'proposalTCO_data': {
            'contract_service_type': proposal_tco.contract_service_type,
            'total_supply_spend': float(proposal_tco.total_supply_spend),
            'total_service_spend': float(proposal_tco.total_service_spend),
            'total_lease_spend': float(proposal_tco.total_lease_spend),
            'est_transaction_overhead': float(proposal_tco.est_transaction_overhead),
            'total_sales_orders': float(proposal_tco.total_sales_orders),
            'total_service_orders': float(proposal_tco.total_service_orders),
            'proposal_id': proposal_tco.proposal_id
        },
        'proposalTCO_info': json.dumps({
            'total_supply_spend': float(proposal_tco.total_supply_spend),
            'total_service_spend': float(proposal_tco.total_service_spend),
            'total_lease_spend': float(proposal_tco.total_lease_spend),
            'est_transaction_overhead': float(proposal_tco.est_transaction_overhead),
            'total_sales_orders': float(proposal_tco.total_sales_orders),
            'total_service_orders': float(proposal_tco.total_service_orders),
            'proposal_id': proposal_tco.proposal_id
        }),
        'proposal_tco_items': proposal_tco_items
    }

    return render(request, 'rep/newProposal/TCO.html', context)

@login_required
def tco_device_details(request, proposal_id):
  device = ProposalTCOItem.objects.get(id=request.GET['id'])
  return JsonResponse({"device": model_to_dict(device), "printer": model_to_dict(device.printer)})


# get TCO module
@login_required
def proposal_get_tco(request, proposal_id):
    proposalTCO_settings = ProposalTCO.objects.get(proposal_id=proposal_id)
    context_raw = {
        'proposalTCO_id': proposalTCO_settings.id,
        'contract_service_type': proposalTCO_settings.contract_service_type,
        'total_supply_spend': float(proposalTCO_settings.total_supply_spend),
        'total_service_spend': float(proposalTCO_settings.total_service_spend),
        'total_lease_spend': float(proposalTCO_settings.total_lease_spend),
        'est_transaction_overhead': float(proposalTCO_settings.est_transaction_overhead),
        'total_sales_orders': float(proposalTCO_settings.total_sales_orders),
        'total_service_orders': float(proposalTCO_settings.total_service_orders),
        'proposal_id': proposalTCO_settings.proposal_id
    }
    #print (json.dumps(context_raw))
    return JsonResponse(json.dumps(context_raw), safe=False)


@login_required
def save_proposed_cpp(request):
    data = json.loads(request.POST['data'])
    proposal_id = data.get('proposal_id')
    proposed_cpp = data.get('proposed_cpp')
    value = data.get('value')

    proposal = Proposal.objects.get(id=proposal_id)
    tiered_values = TieredValue.objects.filter(proposal=proposal).first()

    setattr(tiered_values, proposed_cpp, value)
    tiered_values.save()
    return JsonResponse({'status': 'Success', 'msg': 'Item Saved'})


def setup_part_details_for_costs(printer_short_model, proposal):
    printer = Printer.objects.get(short_model=printer_short_model)
    mgmt_assumption = proposal.management_assumptions
    toner_after_reman = mgmt_assumption.toner_after_reman
    toner_after_oem_smp = mgmt_assumption.toner_after_oem_smp
    default_toner_type = proposal.default_toner_type

    effective_mono_yield = mgmt_assumption.effective_mono_yield
    effective_color_yield = mgmt_assumption.effective_color_yield

    def get_printer_part_cost_details(color, part_django_model, makeup, company):
        effective_yield = effective_color_yield if color != 'mono' else effective_mono_yield
        part_dict = {}
        if makeup is True:

            part_obj = get_device_part(printer, part_django_model, color, default_toner_type, toner_after_reman, toner_after_oem_smp, company)
            if part_obj is None:
                return None

            if getattr(part_obj, 'new_price', False):
                # streetfighter item with new price set
                price = part_obj.new_price
                part_obj = part_obj.original_part
            elif hasattr(part_obj, 'original_part'):
                # streetfigher item but no new price set
                part_obj = part_obj.original_part
                price = part_obj.price
            else:
                # not a streetfighter item
                price = part_obj.price
            if part_obj.manufacturer == REMAN:
                price = (price * (1 - (mgmt_assumption.reman_rebate / 100))) + mgmt_assumption.toner_shipping_price
            elif part_obj.manufacturer == OEM:
                price = (price * (1 - (mgmt_assumption.oem_rebate / 100))) + mgmt_assumption.toner_shipping_price
            else:
                price = ((price * (1 + mgmt_assumption.distro_markup)) * (1 - (mgmt_assumption.oem_smp_rebate / 100))) + mgmt_assumption.toner_shipping_price

            part_dict['price'] = price
            part_dict['yield_amount'] = part_obj.yield_amount * effective_yield
            part_dict['gate'] = part_obj.gate
        else:
            part_dict['price'] = 0.0
            part_dict['yield_amount'] = -1.0

        return part_dict

    return get_printer_part_cost_details

def calculate_mono_cpp(short_model, proposal_id, company):
    printer = Printer.objects.get(short_model=short_model)
    proposal = Proposal.objects.get(id=proposal_id)

    get_printer_part_cost_details = setup_part_details_for_costs(short_model, proposal)

    toner_mono = drum_mono = developer_mono = ''

    if proposal.street_fighter_status == Proposal.APPROVED:
        toner_mono = get_printer_part_cost_details('mono', StreetFighterToner,
                                                   printer.mono_toner, company)
        drum_mono = get_printer_part_cost_details('mono', StreetFighterDrum,
                                                  printer.mono_drum, company)
        developer_mono = get_printer_part_cost_details('mono', StreetFighterDeveloper,
                                                       printer.mono_developer,
                                                       company)
    if not toner_mono:
        toner_mono = get_printer_part_cost_details('mono', Toner, printer.mono_toner, company)
    if not drum_mono:
        drum_mono = get_printer_part_cost_details('mono', Drum, printer.mono_drum, company)
    if not developer_mono:
        developer_mono = get_printer_part_cost_details('mono', Developer, printer.mono_developer, company)

    if not toner_mono or not drum_mono or not developer_mono:
        return None

    if toner_mono['yield_amount'] == -1.0 and drum_mono['yield_amount'] == -1.0 and developer_mono['yield_amount'] == -1.0:
        return None

    toner_cpp = float(toner_mono['price']) / float(toner_mono['yield_amount'])
    drum_cpp = float(drum_mono['price']) / float(drum_mono['yield_amount']) if drum_mono['yield_amount'] != -1 else 0
    dev_cpp = float(developer_mono['price']) / float(developer_mono['yield_amount']) if drum_mono['yield_amount'] != -1 else 0
    black_cost_per_page = toner_cpp + drum_cpp + dev_cpp
    return Decimal(black_cost_per_page)

def calculate_color_cpp(short_model, proposal_id, company):
    printer = Printer.objects.get(short_model=short_model)
    proposal = Proposal.objects.get(id=proposal_id)

    get_printer_part_cost_details = setup_part_details_for_costs(short_model, proposal)

    toner_cyan = toner_magenta = toner_yellow = ''
    drum_cyan = drum_magenta = drum_yellow = ''
    developer_cyan = developer_magenta = developer_yellow = ''

    if proposal.street_fighter_status == Proposal.APPROVED:
        toner_cyan = get_printer_part_cost_details(
            'cyan', StreetFighterToner, printer.cyan_toner, company
        )
        toner_yellow = get_printer_part_cost_details(
            'yellow', StreetFighterToner, printer.yellow_toner, company
        )
        toner_magenta = get_printer_part_cost_details(
            'magenta', StreetFighterToner, printer.magenta_toner, company
        )
        drum_cyan = get_printer_part_cost_details(
            'cyan', StreetFighterDrum, printer.cyan_drum, company
        )
        drum_yellow = get_printer_part_cost_details(
            'yellow', StreetFighterDrum, printer.yellow_drum, company
        )
        drum_magenta = get_printer_part_cost_details(
            'magenta', StreetFighterDrum, printer.magenta_drum, company
        )
        developer_cyan = get_printer_part_cost_details(
            'cyan', StreetFighterDeveloper, printer.cyan_developer, company
        )
        developer_yellow = get_printer_part_cost_details(
            'yellow', StreetFighterDeveloper, printer.yellow_developer, company
        )
        developer_magenta = get_printer_part_cost_details(
            'magenta', StreetFighterDeveloper,printer.magenta_developer,
            company
        )

    if not toner_cyan:
        toner_cyan = get_printer_part_cost_details(
            'cyan', Toner, printer.cyan_toner, company
        )
    if not toner_yellow:
        toner_yellow = get_printer_part_cost_details(
            'yellow', Toner, printer.yellow_toner, company
        )
    if not toner_magenta:
        toner_magenta = get_printer_part_cost_details(
            'magenta', Toner, printer.magenta_toner, company
        )

    if not drum_cyan:
        drum_cyan = get_printer_part_cost_details(
            'cyan', Drum, printer.cyan_drum, company
        )
    if not drum_yellow:
        drum_yellow = get_printer_part_cost_details(
            'yellow', Drum, printer.yellow_drum, company
        )
    if not drum_magenta:
        drum_magenta = get_printer_part_cost_details(
            'magenta', Drum, printer.magenta_drum, company
        )

    if not developer_cyan:
        developer_cyan = get_printer_part_cost_details(
            'cyan', Developer, printer.cyan_developer, company
        )
    if not developer_yellow:
        developer_yellow = get_printer_part_cost_details(
            'yellow', Developer, printer.yellow_developer, company
        )
    if not developer_magenta:
        developer_magenta = get_printer_part_cost_details(
            'magenta', Developer, printer.magenta_developer, company
        )

    #TODO: if missing one of the colored parts, fill with existing colored part
    if not toner_cyan or not toner_yellow or not toner_magenta or not drum_cyan or not drum_yellow or not drum_magenta or not developer_cyan or not developer_yellow or not developer_magenta:
        print(printer, 'was supposed to have part according to makeup, but was missing a part in the database')
        return None

    mono_cost_per_page = calculate_mono_cpp(short_model, proposal_id, company)
    if toner_cyan['yield_amount'] == -1.0 and toner_yellow['yield_amount'] == -1.0 and toner_magenta['yield_amount'] == -1.0 and drum_cyan['yield_amount'] == -1.0 and drum_yellow['yield_amount'] == -1.0 and drum_magenta['yield_amount'] == -1.0 and developer_cyan['yield_amount'] == -1.0 and developer_yellow['yield_amount'] == -1.0 and developer_magenta['yield_amount'] == -1.0:
        return None

    if mono_cost_per_page is None:
        #TODO: this should never happen unless we are missing a part
        return None

    color_cost_per_page = mono_cost_per_page + Decimal(toner_cyan['price']) / Decimal(toner_cyan['yield_amount']) + Decimal(toner_yellow['price']) / Decimal(toner_yellow['yield_amount']) + Decimal(toner_magenta['price']) / Decimal(toner_magenta['yield_amount']) + Decimal(drum_cyan['price']) / Decimal(drum_cyan['yield_amount']) + Decimal(drum_yellow['price']) / Decimal(drum_yellow['yield_amount']) + Decimal(drum_magenta['price']) / Decimal(drum_magenta['yield_amount']) + Decimal(developer_cyan['price']) / Decimal(developer_cyan['yield_amount'])  + Decimal(developer_yellow['price'])  / Decimal(developer_yellow['yield_amount']) + Decimal(developer_magenta['price']) / Decimal(developer_magenta['yield_amount'])

    return Decimal(color_cost_per_page)

def calculate_service_rate(printer, proposal, mgmt_assumpts, company, page_costs):
    exchange_rate = 0
    #TODO: Make model to store brands that company commonly sells and use that instead of hard-coding
    if printer.make.name == 'Oth':
        exchange_rate += 3
    elif printer.make.name == 'Samsung':
        exchange_rate += 2
    else:
        exchange_rate += 1

    get_printer_part_cost_details = setup_part_details_for_costs(printer.short_model, proposal)
    gate = get_printer_part_cost_details('mono', Toner, printer.mono_toner, company)['gate']
    exchange_rate += float(gate.us_rate)

    if  printer.is_color_device:
        exchange_rate += 4
    else:
        exchange_rate += 2

    if page_costs.source == 'Fixed':
        exchange_rate = float(page_costs.service_cpp) * 1000

    # The proportion_fleet_offsite field is no longer used
    proportion_fleet_offsite = float(proposal.proportion_fleet_offsite)
    # These are the percentage of devices on the proposal which are in non-local "zones"
    z1_percent = float(proposal.zone_01)
    z2_percent = float(proposal.zone_02)
    z3_percent = float(proposal.zone_03)
    # These are the percentage to inflate service costs for each non-local "zone"
    z1_inflate = float(mgmt_assumpts.inflate_out_of_area)
    z2_inflate = float(mgmt_assumpts.tier2_inflate)
    z3_inflate = float(mgmt_assumpts.tier3_inflate)
    # The device percent times the zone inflate value gives the zone service cost increase
    z1_bump = z1_percent * z1_inflate
    z2_bump = z2_percent * z2_inflate
    z3_bump = z3_percent * z3_inflate
    # The sum of the increases provides the total service cost percent increase
    total_service_cost_increase = z1_bump + z2_bump + z3_bump
    # The target service margin must be apportioned across the contract term
    # remove -1 and  - ((proposal.term / 12) / 100)
    margin_service_rate = float(mgmt_assumpts.target_margin_service)
    # New calculation taking into account multiple service zones and percentages
    scaled_service_cost_multiplier = (1 + total_service_cost_increase) / (1 - margin_service_rate)
    # the following line is the old scaled cost multiplier calculation before adding zones
    # scaled_service_cost_multiplier = (1 + float(mgmt_assumpts.inflate_out_of_area) * proportion_fleet_offsite) / (1 - margin_service_rate)


    exchange_rate = exchange_rate / 1000.0 * float(mgmt_assumpts.exchange_service_to_currency)

    old_device_inflate = float(mgmt_assumpts.old_inflate_percent)
    if year_difference(printer.release_date, datetime.today().date()) >= mgmt_assumpts.inflate_older_than:
        exchange_rate = exchange_rate * (1 + old_device_inflate)

    service_level = proposal.contract_service_level.name
    if service_level == 'Gold':
        base_service_rate = scaled_service_cost_multiplier * exchange_rate * (1 + float(mgmt_assumpts.gold_service))
    elif service_level == 'Platinum':
        base_service_rate = scaled_service_cost_multiplier * exchange_rate * (1 + float(mgmt_assumpts.platinum_service))
    else:
        base_service_rate = scaled_service_cost_multiplier * exchange_rate

    # Determine the cost multiplier if cost must be adjusted based on proposal duration (GEL 10-15-2019)
    if mgmt_assumpts.allow_term_offsets:
        if proposal.term == 12:
            cost_multiplier = 1 - mgmt_assumpts.cost_offset_12month
        elif proposal.term == 24:
            cost_multiplier = 1 - mgmt_assumpts.cost_offset_24month
        elif proposal.term == 36:
            cost_multiplier = 1 - mgmt_assumpts.cost_offset_36month
        elif proposal.term == 48:
            cost_multiplier = 1 - mgmt_assumpts.cost_offset_48month
        else:
            cost_multiplier = 1 - mgmt_assumpts.cost_offset_60month
    else:
        cost_multiplier = 1
    # Adjust the service rate to inflate the "cost" (GEL 10-15-2019)
    base_service_rate = base_service_rate / float(cost_multiplier)

    # Remove the next line so there isn't a minimum.
    # base_service_rate = base_service_rate if base_service_rate >= 0.006 else 0.006

    contract_type = proposal.contract_service_type
    if contract_type == 'supplies_only':
        service_rate = 0
    elif contract_type == 'service_only':
        service_rate = (1 + float(mgmt_assumpts.service_only)) * base_service_rate
    else:
        service_rate = base_service_rate

    return Decimal(service_rate)


#   This DEF is used in imports.py
def get_scaled_toner_costs(management_assumptions, proposal, printer, company, page_costs):
    toner_costs = {}
    # remove -1 and - ((proposal.term / 12) / 100))
    margin_toner_rate = Decimal(float(management_assumptions.target_margin_toner))

    if management_assumptions.allow_term_offsets:
        if proposal.term == 12:
            cost_multiplier = 1 - management_assumptions.cost_offset_12month
        elif proposal.term == 24:
            cost_multiplier = 1 - management_assumptions.cost_offset_24month
        elif proposal.term == 36:
            cost_multiplier = 1 - management_assumptions.cost_offset_36month
        elif proposal.term == 48:
            cost_multiplier = 1 - management_assumptions.cost_offset_48month
        else:
            cost_multiplier = 1 - management_assumptions.cost_offset_60month
    else:
        cost_multiplier = 1

    black_cost_per_page = calculate_mono_cpp(short_model=printer.short_model, proposal_id=proposal.id, company=company)
    color_cost_per_page = calculate_color_cpp(short_model=printer.short_model, proposal_id=proposal.id, company=company) if printer.is_color_device else None

    toner_costs['scaled_mono_cost'] = (black_cost_per_page / cost_multiplier) / (1 - margin_toner_rate)
    toner_costs['scaled_color_cost'] = (color_cost_per_page / cost_multiplier) / (1 - margin_toner_rate) if printer.is_color_device else 0
    toner_costs['raw_mono_cost'] = (black_cost_per_page / cost_multiplier)
    toner_costs['raw_color_cost'] = (color_cost_per_page / cost_multiplier) if printer.is_color_device else 0
    toner_costs['scaled_service_cost'] = calculate_service_rate(printer, proposal, management_assumptions, company, page_costs)

    return toner_costs


# @login_required
@csrf_exempt
@require_http_methods(['POST'])
def get_network_device_details(request):
    post_data = request.POST.dict()
    try:
        if(request.user.is_anonymous):
            company_key = post_data.get('company_key')
            company = Company.objects.get(self_service_key=company_key)
        else:
            company = request.user.mps_user.company
        proposal = Proposal.objects.get(id=post_data['proposal_id'])
        mgmt_assumpts = proposal.management_assumptions

        if mgmt_assumpts.allow_term_offsets:
            if proposal.term == 12:
                cost_multiplier = 1 - mgmt_assumpts.cost_offset_12month
            elif proposal.term == 24:
                cost_multiplier = 1 - mgmt_assumpts.cost_offset_24month
            elif proposal.term == 36:
                cost_multiplier = 1 - mgmt_assumpts.cost_offset_36month
            elif proposal.term == 48:
                cost_multiplier = 1 - mgmt_assumpts.cost_offset_48month
            else:
                cost_multiplier = 1 - mgmt_assumpts.cost_offset_60month
        else:
            cost_multiplier = 1
        
        # 1. printer costs
        all_printer_costs = PrinterCost.objects.filter(printer__id=post_data['device_id'], company=company)
        printer_costs = {}
        for p_cost in all_printer_costs:
            printer_costs[p_cost.id] = {
                'id': p_cost.id,
                'model_name': p_cost.long_model,
                'outCost': float(p_cost.out_cost or 0.00),
                'msrp': float(p_cost.msrp_cost or 0.00),
                'carePackCost': float(p_cost.care_pack_cost or 0.00),
            }

        # 2. printer details
        #    add avm values to data pool
        printer = Printer.objects.get(id=post_data['device_id'])
        printer_details = {
            'printer_is_color_type': printer.is_color_device,
            'release_date': printer.release_date,
            'make': printer.make.name,
            'device_type': printer.device_type,
            'avm_color': printer.avm_color,
            'avm_mono': printer.avm_mono,
            'retail_mono': float(printer.retail_mono or 0.00),
            'retail_color': float(printer.retail_color or 0.00),
        }
        
        # 3. toner costs
        toners_cost = {}
        # removed -1 and - ((proposal.term / 12) / 100)
        margin_toner_rate = float(mgmt_assumpts.target_margin_toner) 

        black_cost_per_page = calculate_mono_cpp(short_model=printer.short_model, proposal_id=post_data['proposal_id'], company=company)
        color_cost_per_page = calculate_color_cpp(short_model=printer.short_model, proposal_id=post_data['proposal_id'], company=company) if printer.is_color_device else None

        if black_cost_per_page is None or (printer.is_color_device and color_cost_per_page is None):
            toners_cost['warning'] = 'No avaiable toner or drum or developer for this printer model in databse'
            context = {
                'printer_costs': printer_costs,
                'printer_details': printer_details,
                'toners_costs': toners_cost
            }
            return JsonResponse(context)

        toners_cost['scaled_mono_cost'] = (black_cost_per_page / cost_multiplier) / (1 - Decimal(margin_toner_rate))
        toners_cost['scaled_color_cost'] = (color_cost_per_page / cost_multiplier) / (1 - Decimal(margin_toner_rate)) if printer.is_color_device else 0
        
        toners_cost['raw_mono_cost'] = (black_cost_per_page / cost_multiplier)
        toners_cost['raw_color_cost'] = (color_cost_per_page / cost_multiplier) if printer.is_color_device else 0

        toners_cost['raw_mono_cost'] = (black_cost_per_page / cost_multiplier)
        toners_cost['raw_color_cost'] = (color_cost_per_page / cost_multiplier) if printer.is_color_device else 0

        # 4. service costs
        page_costs = PageCost.objects.get(printer__id=post_data['device_id'], company=company)
        
        def_base_volume_mono = 0 if page_costs.def_base_volume_mono is None else page_costs.def_base_volume_mono
        def_base_volume_color = 0 if page_costs.def_base_volume_color is None else page_costs.def_base_volume_color

        page_cost_details = {
            'pagecost_id': page_costs.id,
            'def_base_rate_mono': float(page_costs.def_base_rate_mono or 0.00),
            'def_base_rate_color': float(page_costs.def_base_rate_color or 0.00),
            'def_base_volume_mono': def_base_volume_mono,
            'def_base_volume_color': def_base_volume_color
        }
        service_rate = calculate_service_rate(printer, proposal, mgmt_assumpts, company, page_costs)
        toners_cost['scaled_service_cost'] = service_rate

        toners_cost['mono_cpp'] = (toners_cost['raw_mono_cost'] + (service_rate * (1 - mgmt_assumpts.target_margin_service)))
        toners_cost['color_cpp'] = (toners_cost['raw_mono_cost'] + toners_cost['raw_color_cost'] + (service_rate * (1 - mgmt_assumpts.target_margin_service)))

        accs = Accessory.objects.filter(printer=printer, company=company)
        accessories = {}
        for acc in accs:
            accessories[acc.id] = {
                'part_number': acc.part_number,
                'description': acc.description,
                'out_cost': acc.out_cost,
                'msrp_cost': acc.msrp_cost
            }

        context = {
            'printer_costs': printer_costs,
            'printer_details': printer_details,
            'toners_costs': toners_cost,
            'accessories': accessories,
            'page_cost_details': page_cost_details
        }
    except Exception as e:
        print("Exception: " + str(e))
        context = {
            'printer_costs': {},
            'printer_details': {},
            'toners_costs': {
                'warning': 'No avaiable toner or drum or developer for this printer model in databse'
            },
            'accessories': {}
        }
    return JsonResponse(context)

@login_required
@require_http_methods(['POST'])
def get_non_network_device_details(request):
    post_data = request.POST.dict()
    printer = Printer.objects.get(short_model=post_data['network_device_short_name'])
    company = request.user.mps_user.company
    proposal = Proposal.objects.get(id=post_data['proposal_id'])
    mgmt_asmpt = proposal.management_assumptions
    
    monthly_costs = 0
    non_network_details = {}
    # Add exception handling for printers without PageCost entries (GEL)
    try:
        page_costs = PageCost.objects.get(printer__id=post_data['device_id'], company=company)
    except Exception as e:
        non_network_details['warning'] = 'No avaiable toner or drum or developer for this printer model in databse'
        context = {
            'non_network_unit_price': json.dumps(monthly_costs, cls=DjangoJSONEncoder),
            'non_network_details': json.dumps(non_network_details, cls=DjangoJSONEncoder)
        }
        return HttpResponse(json.dumps(context), content_type="application/json")

    non_network_details['printer_is_color_type'] = printer.is_color_device
    # 1. unit monthly cost
    non_network_device_margin = mgmt_asmpt.non_network_margin
    annual_black_cartridges = float(mgmt_asmpt.annual_mono_cartridges)
    percentage_color = float(mgmt_asmpt.percentage_color)
    mk_expectancy = float(mgmt_asmpt.maintenance_kit_replaced_years)

    toner = Toner.objects.get(manufacturer='OEM', part_color='mono', printer=printer, company=company)
    oem_black_pages = toner.yield_amount

    monthly_volume_from_black_yield = math.ceil(oem_black_pages * annual_black_cartridges / 12) if annual_black_cartridges >= 0 else 0

    color_monthly_pages = monthly_volume_from_black_yield * percentage_color if printer.is_color_device else 0
    mono_monthly_pages = monthly_volume_from_black_yield - color_monthly_pages

    if monthly_volume_from_black_yield == 0:
        kit_yield = float(printer.duty_cycle)
        monthly_volume_from_kit_yield = math.ceil(math.ceil(kit_yield/(mk_expectancy*12.0)))
        color_monthly_pages = monthly_volume_from_kit_yield * percentage_color if printer.is_color_device else 0
        mono_monthly_pages = monthly_volume_from_kit_yield - color_monthly_pages

    # check proposal contract service type
    base_cpp_mono = calculate_mono_cpp(post_data['network_device_short_name'], post_data['proposal_id'], company)
    base_cpp_color = calculate_color_cpp(post_data['network_device_short_name'], post_data['proposal_id'], company) if printer.is_color_device else None

    if base_cpp_mono is None or (printer.is_color_device and base_cpp_color is None):
        non_network_details['warning'] = 'No avaiable toner or drum or developer for this printer model in databse'
        context = {
            'non_network_unit_price': json.dumps(monthly_costs, cls=DjangoJSONEncoder),
            'non_network_details': json.dumps(non_network_details, cls=DjangoJSONEncoder)
        }
        return HttpResponse(json.dumps(context), content_type="application/json")

    # add service costs if needed
    service_rate = calculate_service_rate(printer, proposal, mgmt_asmpt, company, page_costs) * (1 - mgmt_asmpt.target_margin_service)

    # add supplies only bump here (GEL 2020-04-07)
    if proposal.contract_service_type == 'service_only':
        cpp_mono = service_rate
        cpp_color = service_rate if printer.is_color_device else 0
    elif proposal.contract_service_type == 'supplies_only':
        cpp_mono = base_cpp_mono
        cpp_color = base_cpp_color if printer.is_color_device else 0
    else:
        cpp_mono = base_cpp_mono + service_rate
        cpp_color = base_cpp_color + service_rate if printer.is_color_device else 0

    monthly_costs = (cpp_mono * Decimal(mono_monthly_pages) + cpp_color * Decimal(color_monthly_pages)) / (1 - Decimal(non_network_device_margin))
    non_net_cost = monthly_costs * (1 - Decimal(non_network_device_margin))

    # mono pages * (mono_rate + service_rate) + color_pages * (color + service)

    # 2. non-network device details
    rate = 0
    non_margin = 0
    if mgmt_asmpt.pay_non_network_commission:
        if mgmt_asmpt.commission_type == 'flat_margin':
            rate = float(mgmt_asmpt.percent_margin_flat_rate)
            non_margin = monthly_costs - non_net_cost
        elif mgmt_asmpt.commission_type == 'flat_revenue':
            rate = float(mgmt_asmpt.percentage_revenue_flat_rate)
            non_margin = monthly_costs
        elif mgmt_asmpt.commission_type == 'blended_margin':
            rate = float(mgmt_asmpt.margin_rate_printers) if printer.device_type == 'printer' else float(mgmt_asmpt.margin_rate_copiers)
            non_margin = monthly_costs - non_net_cost
        elif mgmt_asmpt.commission_type == 'blended_revenue':
            rate = float(mgmt_asmpt.revenue_rate_printers) if printer.device_type == 'printer' else float(mgmt_asmpt.revenue_rate_copiers)
            non_margin = monthly_costs

    non_network_details['non_network_commission'] = non_margin * Decimal(rate)

    context = {
        'non_network_unit_price': monthly_costs,
        'non_network_details': non_network_details,
    }
    return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder), content_type="application/json")

@login_required
def get_street_fighter_items(request, alert_id):
    alert = ManagerAlert.objects.get(id=alert_id, company=request.user.mps_user.company)

    sf_items = []
    sf_items += get_sf_item_info_list(alert.proposal, StreetFighterToner)
    sf_items += get_sf_item_info_list(alert.proposal, StreetFighterDrum)
    sf_items += get_sf_item_info_list(alert.proposal, StreetFighterDeveloper)

    context = {
        'sf_items': sf_items,
        'alert_id': alert_id,
        'proposal': alert.proposal
    }

    return JsonResponse({'items': render_to_string('manager/alerts/streetFighterItems.html', context)})

@login_required
def save_street_fighter_costs(request, alert_id):
    items = json.loads(request.POST['items'])
    alert = ManagerAlert.objects.get(id=alert_id)

    for item in items:
        part_type = item['part_type']
        if part_type == Toner().part_type:
            update_street_fighter_costs(item, StreetFighterToner, alert.proposal.id)
        elif part_type == Drum().part_type:
            update_street_fighter_costs(item, StreetFighterDrum, alert.proposal.id)
        elif part_type == Developer().part_type:
            update_street_fighter_costs(item, StreetFighterDeveloper, alert.proposal.id)
        else:
            return JsonResponse({'status': 'Error', 'msg': 'Error saving. Could not find ' + item['part_id']})

    # TODO: save the items!
    return JsonResponse({'status': 'Success', 'msg': 'Items Saved'})

@login_required
def accept_street_fighter_pricing(request, proposal_id):
    proposal = Proposal.objects.get(id=proposal_id)
    proposal.street_fighter_status = Proposal.APPROVED
    proposal.save()
    return JsonResponse({'status': 'Success', 'msg': 'Street fighter pricing approved'})

@login_required
def decline_street_fighter_pricing(request, proposal_id):
    proposal = Proposal.objects.get(id=proposal_id)
    proposal.street_fighter_status = Proposal.DECLINED
    proposal.save()
    return JsonResponse({'status': 'Success', 'msg': 'Street fighter pricing declined'})

@login_required
def request_street_fighter_pricing(request):
    try:
        proposal = Proposal.objects.get(id=request.POST['proposal_id'], sales_rep=request.user.mps_user)

        delete_existing_sf_items(proposal)
        if create_street_fighter_items(proposal):
            proposal.street_fighter_status = Proposal.PENDING
            proposal.save()

            sf_alert = ManagerAlert(proposal=proposal, company=request.user.mps_user.company,
                                    alert_type=ManagerAlert.STREET_FIGHTER, create_date=datetime.now())
            sf_alert.save()
            return HttpResponse('Request Sent!')
        else:
            return HttpResponseBadRequest('There was a problem making the request!')
    except Proposal.DoesNotExist:
        return HttpResponseBadRequest('Not a valid proposal')

@login_required
def proposal_preview(request, proposal_id):
    proposal = Proposal.objects.get(id=proposal_id)

    sales_rep = MPS_User.objects.get(pk=proposal.sales_rep.id)
    company = Company.objects.get(pk=sales_rep.company.id)

    term = proposal.term if proposal.term is not None else -1
    contract_type = proposal.contract_service_type if proposal.contract_service_type is not None else -1
    manufacturer = proposal.default_toner_type if proposal.default_toner_type is not None else -1
    # The field proportion_fleet_offsite now actually stores the percent "local" devices.  Needs renamed.
    fleet_outside_location = float(proposal.proportion_fleet_offsite) if proposal.proportion_fleet_offsite is not None else -1
    zone_01 = float(proposal.zone_01) if proposal.zone_01 is not None else -1
    zone_02 = float(proposal.zone_02) if proposal.zone_02 is not None else -1
    zone_03 = float(proposal.zone_03) if proposal.zone_03 is not None else -1
    autopopbase =  proposal.auto_populate_base_info if proposal.auto_populate_base_info is not None else -1,
    service_level = proposal.contract_service_level.name if proposal.contract_service_level is None else -1

    context = {
        'proposal_details': {
            'proposal_id': proposal_id,
            'proposal_term': term,
            'proposal_contractType': contract_type,
            'proposal_manufacturer': manufacturer,
            # The proportion_fleet_offsite field is now stores the "local" percent
            'proposal_propotionFleetOutsideLocation': fleet_outside_location,
            'proposal_zone_01': zone_01,
            'proposal_zone_02': zone_02,
            'proposal_zone_03': zone_03,
            'auto_pop_base': autopopbase,
            'proposal_serviceLevel': service_level
        },
        'proposal_id': proposal_id,
        'client': proposal.client.organization_name,
        'company_id': company.id
    }

    return render(request, 'rep/newProposal/proposalPreview.html', context)

@login_required
def import_home(request):
    return render(request, 'importHome.html')

@login_required
def summary_page(request):
    return render(request, 'rep/summarypage.html')

@login_required
@require_http_methods(['GET'])
def get_management_assumptions(request):
    management_assumptions = ManagementAssumption.objects.get(company=request.user.mps_user.company)
    equipment_inflate = management_assumptions.equipment_inflate
    accessory_inflate = management_assumptions.accessory_inflate
    target_margin_equipment = management_assumptions.target_margin_equipment
    managed_cartridge_inflate = management_assumptions.managed_cartridge_inflate
    return JsonResponse({'equipment_inflate': equipment_inflate, 'accessory_inflate': accessory_inflate, 'managed_cartridge_inflate': managed_cartridge_inflate})

#=====utlity===============================================================
def year_difference(date1, date2):
    # both dates need to be in datetime.date format
    later = max(date1, date2)
    earlier = min(date1, date2)

    gap = later.year - earlier.year
    if later.month < earlier.month or (later.month == earlier.month and later.day < earlier.day):
        gap -= 1
    return gap

@login_required
def my_account_equipment(request):
    mps_user = MPS_User.objects.get(user=request.user)
    printers_offered = list(PrinterCost.objects.filter(company=mps_user.company).order_by('printer__short_model', 'long_model').select_related('printer')) # TODO filter to user's company when we have multi-tenancy figured out
    accessories = Accessory.objects.filter(company=mps_user.company).order_by('part_number')

    arranged = defaultdict(lambda: {'printers': [], 'accessories': []})

    for p_o in printers_offered:
        arranged[p_o.printer_id]['printers'].append(p_o)
        arranged[p_o.printer_id]['printer_family'] = p_o.printer

    for accessory in accessories:
        arranged[accessory.printer_id]['accessories'].append(accessory)

    context = {
        'arranged': dict(arranged),
    }
    return render(request, 'manager/myAccount/equipment.html', context=context)

@login_required
def my_account_supplies(request):
    toners = Toner.objects.filter(company=request.user.mps_user.company).select_related('printer').order_by('printer__short_model')
    def supply_default():
        return {
            'toners': [],
            'drums': [],
            'developers': [],
        }

    oem = defaultdict(supply_default)
    oem_smp = defaultdict(supply_default)
    reman = defaultdict(supply_default)

    for toner in toners:
        if toner.manufacturer == 'OEM':
            oem[toner.printer_id]['toners'].append(toner)
            oem[toner.printer_id]['printer'] = toner.printer
        elif toner.manufacturer == 'OEM_SMP':
            oem_smp[toner.printer_id]['toners'].append(toner)
            oem_smp[toner.printer_id]['printer'] = toner.printer
        elif toner.manufacturer == 'REMAN':
            reman[toner.printer_id]['toners'].append(toner)
            reman[toner.printer_id]['printer'] = toner.printer

    context = {
        'oem': dict(oem),
        'oem_smp': dict(oem_smp),
        'reman': dict(reman),
    }

    return render(request, 'manager/myAccount/supplies.html', context=context)

@login_required
def my_account_service(request):
    page_costs = PageCost.objects.filter(company=request.user.mps_user.company).select_related('printer').order_by('printer__short_model')

    context = {
        'page_costs': page_costs,
    }

    return render(request, 'manager/myAccount/service.html', context=context)

@login_required
def my_account_tcv(request):
    company = request.user.mps_user.company
    management_assumption = ManagementAssumption.objects.filter(
        company_id=company.id
    )
    accepted_proposals = Proposal.objects.filter(is_approved=True)
    if len(management_assumption):
        accepted_proposals = accepted_proposals.filter(
            management_assumptions_id=management_assumption[0].id
        )

    proposals = []
    for proposal in accepted_proposals:
        sales_rep = MPS_User.objects.get(pk=proposal.sales_rep.id)
        sales_rep_user = User.objects.get(pk=sales_rep.user.id)
        sales_rep_name = sales_rep_user.first_name + ' ' + sales_rep_user.last_name

        customer = Client.objects.get(pk=proposal.client.id)

        data = {
            "proposal": proposal,
            "customer_name": customer.organization_name,
            "sales_rep_name": sales_rep_name
        }
        proposals.append(data)

    context = {
        'accepted_proposals': proposals
    }

    return render(request, 'manager/myAccount/tcv.html', context)

@login_required
def view_tcv(request, proposal_id):
    context = {
        'proposal_id': proposal_id
    }
    return render(request, 'manager/myAccount/view_tcv.html', context)

@login_required
def download_tcv(request, proposal_id):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="CA pMPS 2.0 format_v1-1.csv"'

    now = datetime.now()

    fiscal_year = fiscalyear.FiscalYear(now.year)
    fiscalyear.START_MONTH = 11
    fiscalyear.START_DAY = 11

    fiscal_now = FiscalDateTime.now()

    company = Company.objects.get(pk=request.user.mps_user.company.id)
    partner_name = company.name

    ma = ManagementAssumption.objects.get(company=company)

    proposal = Proposal.objects.get(pk=proposal_id)
    client = Client.objects.get(pk=proposal.client.id)
    sales_rep = MPS_User.objects.get(pk=proposal.sales_rep.id)
    sales_rep_user = User.objects.get(pk=sales_rep.user.id)

    end_customer_name = client.organization_name
    end_user_rep = sales_rep_user.first_name + ' ' + sales_rep_user.last_name

    proposal_purchase_items = ProposalPurchaseItem.objects.filter(proposal=proposal)

    total_hw_qty = 0
    network_hardware_ccv = 0
    network_hardware_tcv = 0
    buy_items = []
    lease_items = []
    for item in proposal_purchase_items:
        total_hw_qty = total_hw_qty + item.number_printers_purchased

        if item.long_model.startswith('HP'):
            network_hardware_ccv = network_hardware_ccv + item.out_cost

        network_hardware_tcv = network_hardware_tcv + item.out_cost

        if item.buy_or_lease == 'buy':
            buy_items.append(item)
        elif item.buy_or_lease == 'lease':
            lease_items.append(item)
        elif item.buy_or_lease == 'rent':
            lease_items.append(item)

    proposal_service_items = ProposalServiceItem.objects.filter(proposal=proposal)
    network_service_items = []
    non_network_service_items = []
    for service_item in proposal_service_items:
        if service_item.is_non_network:
            non_network_service_items.append(service_item)
        else:
            network_service_items.append(service_item)

    network_supplies_ccv = 0
    network_supplies_tcv = 0

    if proposal.contract_service_type != 'service_only':
        for item in network_service_items:
            printer = Printer.objects.get(pk=item.printer.id)
            printer_costs = PrinterCost.objects.filter(printer=printer)
            supplies_price = (item.mono_toner_price or 0) + (item.color_toner_price or 0)
            if printer.short_model.startswith('HP'):
                # removed " - Decimal(proposal.term / 12 / 100)"
                network_supplies_ccv = network_supplies_ccv + (supplies_price * (1 - ma.target_margin_toner))

            # removed " - Decimal(proposal.term / 12 / 100)"
            network_supplies_tcv = network_supplies_tcv + (supplies_price * (1 - ma.target_margin_toner))

        network_supplies_ccv = network_supplies_ccv * Decimal(proposal.term)
        network_supplies_tcv = network_supplies_tcv * Decimal(proposal.term)

    network_twop_ccv = 0
    network_twop_tcv = 0

    contract_service_level = ServiceLevel.objects.get(pk=proposal.contract_service_level.id)
    if proposal.contract_service_type != 'supplies_only' and contract_service_level.responseTime == '24 Hours':
        for item in network_service_items:
            printer = Printer.objects.get(pk=item.printer.id)
            printer_costs = PrinterCost.objects.filter(printer=printer)
            if printer_costs.count() > 0:
                if printer.short_model.startswith('HP'):
                    network_twop_ccv = network_twop_ccv + (printer_costs[0].care_pack_cost or 0)

                network_twop_tcv = network_twop_tcv + (printer_costs[0].care_pack_cost or 0)

        network_twop_ccv = network_twop_ccv * Decimal(proposal.term)
        network_twop_tcv = network_twop_tcv * Decimal(proposal.term)

    network_support_ccv = 0
    network_support_tcv = 0

    if proposal.contract_service_type != 'supplies_only':
        for item in network_service_items:
            printer = Printer.objects.get(pk=item.printer.id)
            printer_costs = PrinterCost.objects.filter(printer=printer)
            if printer_costs.count() == 0 or (printer_costs[0].care_pack_cost == None) or (printer_costs[0].care_pack_cost == 0):
                if printer.short_model.startswith('HP'):
                    # removed "- Decimal(proposal.term / 12 / 100)""
                    network_support_ccv = network_support_ccv + (item.service_cost * (1 - ma.target_margin_service))

                # removed "- Decimal(proposal.term / 12 / 100)"
                network_support_tcv = network_support_tcv + (item.service_cost * (1 - ma.target_margin_service))

        network_support_ccv = network_support_ccv * Decimal(proposal.term)
        network_support_tcv = network_support_tcv * Decimal(proposal.term)

    hardware_ccv = network_hardware_ccv
    hardware_tcv = network_hardware_tcv

    supplies_ccv = network_supplies_ccv
    supplies_tcv = network_supplies_tcv

    twop_ccv = network_twop_ccv
    twop_tcv = network_twop_tcv

    support_ccv = network_support_ccv
    support_tcv = network_support_tcv

    total_ccv = hardware_ccv + supplies_ccv + twop_ccv
    total_tcv = hardware_tcv + supplies_tcv + twop_tcv + support_tcv

    writer = csv.writer(response)
    writer.writerow([
        'Fiscal Year',
        'Fiscal Quarter',
        'SubregionName',
        'CARD account',
        'Reported Month',
        'CountryName',
        'Partner Name',
        'End Customer Name',
        'Total CCV',
        'Total TCV',
        'Hardware CCV',
        'Hardware TCV',
        'Supplies CCV',
        'Supplies TCV',
        '2P CCV',
        '2P TCV',
        'Support CCV',
        'Support TCV',
        'SW CCV',
        'SW TCV',
        'Total HW Qty',
        'A3 HW Qty',
        'Deal Notes',
        'End User Rep',
        'Contract Term',
        'Deal Type',
        'Deal Identifier',
        'Created By'
    ])
    writer.writerow([
        fiscal_now.fiscal_year, # Fiscal Year
        'Q' + str(fiscal_now.quarter), # Fiscal Quarter
        'Canada', # SubregionName
        '', # CARD account
        now.strftime('%B'), # Reported Month
        'Canada', # CountryName
        partner_name, # Partner Name
        end_customer_name, # End Customer Name
        round(total_ccv, 2), # Total CCV
        round(total_tcv, 2), # Total TCV
        round(hardware_ccv, 2), # Hardware CCV
        round(hardware_tcv, 2), # Hardware TCV
        round(supplies_ccv, 2), # Supplies CCV
        round(supplies_tcv, 2), # Supplies TCV
        round(twop_ccv, 2), # 2P CCV
        round(twop_tcv, 2), # 2P TCV
        round(support_ccv, 2), # Support CCV
        round(support_tcv, 2), # Support TCV
        0, # SW CCV
        0, # SW TCV
        total_hw_qty, # Total HW Qty
        0, # A3 HW Qty
        '', # Deal Notes
        end_user_rep, # End User Rep
        proposal.term, # Contract Term
        '', # Deal Type
        'New', # Deal Identifier
        '', # Created By
    ])

    return response

# proposal views, these views are client facing


def get_proposal_tco_items(proposal):
    proposal_tco_set = ProposalTCO.objects.filter(proposal=proposal)
    if proposal_tco_set:
        proposal_tco = proposal_tco_set[0]
        proposal_tco_items = ProposalTCOItem.objects.filter(proposalTCO_id=proposal_tco.id)
    else:
        proposal_tco_items = []
    
    return proposal_tco_items

# how to pull cpp to the html
def view_proposal_cpp(request, proposal_id):
    proposal = Proposal.objects.get(pk=proposal_id)
    if request.method == 'POST':
        form = SignatureForm(request.POST)
        if form.is_valid():
            signature = form.cleaned_data.get('signature')
            if signature:
                signature_file_path = draw_signature(signature, as_file=True)

                path = os.path.join(settings.BASE_DIR, 'media/signature_image')
                if not os.path.exists(path):
                    os.makedirs(path)

                signature_image_path = copy2(signature_file_path, path)
                if os.path.exists(signature_file_path):
                    os.remove(signature_file_path)

                proposal.signature_image = signature_image_path.split('media')[-1]
                proposal.status = 'proposal_accepted'
                proposal.save()

    client = Client.objects.get(pk=proposal.client.id)
    sales_rep = MPS_User.objects.get(pk=proposal.sales_rep.id)
    company = Company.objects.get(pk=sales_rep.company.id)
    sales_rep_user = User.objects.get(pk=sales_rep.user.id)
    service_level = ServiceLevel.objects.get(pk=proposal.contract_service_level.id)
    account_settings = AccountSetting.objects.filter(company=company).order_by('-pk')[0]

    context = {
        'proposal': {
            'id': proposal_id,
            'logo': account_settings.logo,
            'term': proposal.term,
            'status': proposal.status,
            'response_time': service_level.responseTime,
            'service_type': proposal.contract_service_type,
            'create_date': proposal.create_date.date,
            'expiration_date': proposal.expiration_date.date,
            'signed_date': proposal.signed_date,
        },
        'client': {
            'name': client.organization_name,
            'contact': client.contact,
            'address': client.address,
            'city': client.city,
            'state': client.state,
            'zipcode': client.zipcode,
            'telephone': client.phone_number,
            'email': client.email,
        },
        'company': {
            'name': company.name,
            'telephone': company.phone_number,
            'owner': company.owner,
        },
        'sales_rep': {
            'first_name': sales_rep_user.first_name,
            'last_name': sales_rep_user.last_name,
            'email': sales_rep_user.email,
        }
    }
    
    context['proposal_signed_date'] = proposal.signed_date or datetime.now().strftime('%d/%m/%Y')
    
    proposal_purchase_items = ProposalPurchaseItem.objects.filter(proposal=proposal)
    proposal_service_items = ProposalServiceItem.objects.filter(proposal=proposal)
    proposal_tco_items = get_proposal_tco_items(proposal)

    count = 0
    buy_items = []
    lease_items = []

    for item in proposal_purchase_items:
        count = count + item.number_printers_purchased
        if item.buy_or_lease == 'buy':
            buy_items.append(item)
            if not context.get('equipment_purchase'):
                context['equipment_purchase'] = True

        elif item.buy_or_lease == 'lease':
            lease_items.append(item)
            if not context.get('equipment_lease'):
                context['equipment_lease'] = True
        elif item.buy_or_lease == 'rent':
            lease_items.append(item)
            if not context.get('equipment_rent'):
                context['equipment_rent'] = True

    buy_total = 0
    for item in buy_items:
        buy_total = buy_total + item.proposed_cost
        long_model = item.long_model if item.long_model is not None else 0
        lease_term = item.lease_term if item.lease_term is not None else 0
        lease_type = 0

    lease_total = 0
    lease_term = 0
    lease_type = 0
    for item in lease_items:
        lease_total = lease_total + item.lease_payment
        long_model = item.long_model if item.long_model is not None else 0
        lease_term = item.lease_term if item.lease_term is not None else 0
        lease_type = item.lease_type

    context['buy_items'] = {
        'total': buy_total,
        'items': buy_items,
    }

    context['lease_items'] = {
        'total': lease_total,
        'items': lease_items,
        'lease_term': lease_term,
        'lease_type': lease_type
    }

    proposal_service_items = ProposalServiceItem.objects.filter(proposal=proposal)
    context['mps_items'] = {
        'count': proposal_service_items.count()
    }
    service_items = []
    service_total = 0
    for item in proposal_service_items:
        printer = Printer.objects.get(pk=item.printer.id)
        device_name = printer.short_model
        cpp_mono = 0
        cpp_color = 0
        base_volume_mono = 0
        base_volume_color = 0
        base_rate_mono = 0
        base_rate_color = 0
        total_mono_pages = 0
        total_color_pages = 0
        mono_price = 0
        color_price = 0
        total_price = 0

        monthly_cost = 0
        if not item.is_non_network:
            monthly_cost = (item.base_rate_mono or 0) + (item.base_rate_color or 0)
            cpp_mono = item.proposed_cpp_mono if item.proposed_cpp_mono > 0 else item.rcmd_cpp_mono
            cpp_color = item.proposed_cpp_color if item.proposed_cpp_color > 0 else item.rcmd_cpp_color
            total_mono_pages = item.total_mono_pages
            total_color_pages = item.total_color_pages
            base_volume_mono = (item.base_volume_mono or 0)
            base_volume_color = (item.base_volume_color or 0)
            base_rate_mono = (item.base_rate_mono or 0)
            base_rate_color = (item.base_rate_color or 0)
            mono_price = (item.base_rate_mono or 0) + (cpp_mono * (total_mono_pages - (item.base_volume_mono or 0)))
            color_price = (item.base_rate_color or 0) + (cpp_color * (total_color_pages - (item.base_volume_color or 0)))
            total_price = mono_price + color_price
            service_total += total_price
        else:
            monthly_cost = item.non_network_cost
            total_mono_pages = 0
            total_color_pages = 0
            base_volume_mono = 0
            base_volume_color = 0
            base_rate_mono = 0
            base_rate_color = 0
            mono_price = 0
            color_price = 0
            total_price = item.non_network_cost
            service_total += total_price

        service_item = {
            'device_name': device_name,
            'monthly_cost': monthly_cost,
            'lease_payment': 0,
            'cpp_mono': cpp_mono,
            'cpp_color': cpp_color,
            'total_mono_pages': total_mono_pages,
            'total_color_pages': total_color_pages,
            'base_volume_mono': base_volume_mono,
            'base_volume_color': base_volume_color,
            'mono_price': mono_price,
            'color_price': color_price,
            'total_price': total_price,
            'info': item,
            'device_count': item.number_printers_serviced
        }

        if item.proposal_purchase_item and item.proposal_purchase_item.id:
          for lease_item in lease_items:
            if lease_item.id == item.proposal_purchase_item.id:
              service_item['lease_payment'] = lease_item.lease_payment

        service_items.append(service_item)


    tco_total = 0
    tco_items = []
    for tco_item in proposal_tco_items:
      item_total = (tco_item.base_rate_mono + ((tco_item.total_mono_pages - tco_item.base_volume_mono) * tco_item.current_cpp_mono)) + (tco_item.base_rate_color + ((tco_item.total_color_pages - tco_item.base_volume_color) * tco_item.current_cpp_color))
      tco_total += item_total
      item = {
        'device_name': tco_item.printer.short_model,
        'base_rate_mono': tco_item.base_rate_mono,
        'base_rate_color': tco_item.base_rate_color,
        'total_base': tco_item.base_rate_mono + tco_item.base_rate_color,
        'monthly_lease': tco_item.monthly_lease_payment,
        'total_mono_pages': tco_item.total_mono_pages,
        'cpp_mono': tco_item.current_cpp_mono,
        'mono_price': tco_item.rcmd_cpp_mono,
        'total_mono_price': tco_item.base_rate_mono + ((tco_item.total_mono_pages - tco_item.base_volume_mono) * tco_item.current_cpp_mono),
        'total_color_pages': tco_item.total_color_pages,
        'cpp_color': tco_item.current_cpp_color,
        'color_price': tco_item.rcmd_cpp_color,
        'total_color_price': tco_item.base_rate_color + ((tco_item.total_color_pages - tco_item.base_volume_color) * tco_item.current_cpp_color),
        'total_price': item_total
      }

      tco_items.append(item)

    if proposal.status == 'in-progress':
        signature_form = SignatureForm()

    elif proposal.status == 'proposal_accepted' and proposal.signature_image.name is not '':
        signature_form = settings.WEB_DOMAIN + proposal.signature_image.url
    else:
        signature_form = None

    context = {
        'service_items': service_items,
        'proposal': {
            'id': proposal_id,
            'logo': account_settings.logo,
            'term': proposal.term,
            'status': proposal.status,
            'response_time': service_level.responseTime,
            'service_type': proposal.contract_service_type,
            'create_date': proposal.create_date.date,
            'expiration_date': proposal.expiration_date.date,
            'signed_date': proposal.signed_date,
        },
        'client': {
            'name': client.organization_name,
            'contact': client.contact,
            'address': client.address,
            'city': client.city,
            'state': client.state,
            'zipcode': client.zipcode,
            'telephone': client.phone_number,
            'email': client.email,
        },
        'company': {
            'name': company.name,
            'telephone': company.phone_number,
        },
        'sales_rep': {
            'first_name': sales_rep_user.first_name,
            'last_name': sales_rep_user.last_name,
            'email': sales_rep_user.email,
        },
        'mps_items': {
          'count': proposal_service_items.count()
        },
        'lease_items': {
          'total': lease_total,
          'items': lease_items,
          'lease_term': lease_term,
          'lease_type': lease_type,
        },
        'buy_items': {
          'total': buy_total,
          'items': buy_items,
        },
        'tco_items': tco_items,
        'total_savings': '${:,.2f}'.format(tco_total - service_total),
        'form': signature_form
    }

    return render(request, 'proposal/' + str(company.id) + '_cpp.html', context)


def view_proposal_nc(request, proposal_id):
    proposal = Proposal.objects.get(pk=proposal_id)
    if request.method == 'POST':
        form = SignatureForm(request.POST)
        if form.is_valid():
            signature = form.cleaned_data.get('signature')
            if signature:
                signature_file_path = draw_signature(signature, as_file=True)

                path = os.path.join(settings.BASE_DIR, 'media/signature_image')
                if not os.path.exists(path):
                    os.makedirs(path)

                signature_image_path = copy2(signature_file_path, path)
                if os.path.exists(signature_file_path):
                    os.remove(signature_file_path)

                proposal.signature_image = signature_image_path.split('media')[-1]
                proposal.status = 'proposal_accepted'
                proposal.save()
    client = Client.objects.get(pk=proposal.client.id)
    sales_rep = MPS_User.objects.get(pk=proposal.sales_rep.id)
    company = Company.objects.get(pk=sales_rep.company.id)
    sales_rep_user = User.objects.get(pk=sales_rep.user.id)
    service_level = ServiceLevel.objects.get(pk=proposal.contract_service_level.id)
    account_settings = AccountSetting.objects.filter(company=company).order_by('-pk')[0]

    context = {
        'proposal': {
            'id': proposal_id,
            'term': proposal.term,
            'logo': account_settings.logo,
            'status': proposal.status,
            'response_time': service_level.responseTime,
            'service_type': proposal.contract_service_type,
            'create_date': proposal.create_date.date,
            'expiration_date': proposal.expiration_date.date,
            'signed_date': proposal.signed_date,
        },
        'client': {
            'name': client.organization_name,
            'contact': client.contact,
            'address': client.address,
            'city': client.city,
            'state': client.state,
            'zipcode': client.zipcode,
            'telephone': client.phone_number,
            'email': client.email,
        },
        'company': {
            'name': company.name,
            'telephone': company.phone_number,
        },
        'sales_rep': {
            'first_name': sales_rep_user.first_name,
            'last_name': sales_rep_user.last_name,
            'email': sales_rep_user.email,
        }
    }

    context['proposal_signed_date'] = proposal.signed_date or datetime.now().strftime('%d/%m/%Y')

    proposal_purchase_items = ProposalPurchaseItem.objects.filter(proposal=proposal)
    count = 0
    buy_items = []
    lease_items = []
    lease_items_4_nc = []
    for item in proposal_purchase_items:
        count = count + item.number_printers_purchased
        if item.buy_or_lease == 'buy':
            buy_items.append(item)
            if not context.get('equipment_purchase'):
                context['equipment_purchase'] = True
        elif item.buy_or_lease == 'lease':
            lease_items.append(item)
            lease_items_4_nc.append(item)
            if not context.get('equipment_lease'):
                context['equipment_lease'] = True
        elif item.buy_or_lease == 'rent':
            lease_items.append(item)
            lease_items_4_nc.append(item)
            if not context.get('equipment_rent'):
                context['equipment_rent'] = True

    buy_total = 0
    for item in buy_items:
        buy_total = buy_total + item.proposed_cost
        long_model = item.long_model if item.long_model is not None else 0
        lease_term = item.lease_term if item.lease_term is not None else 0
        lease_type = 0

    lease_total = 0
    lease_term = 0
    lease_type = 0
    for item in lease_items:
        lease_total = lease_total + item.lease_payment
        long_model = item.long_model if item.long_model is not None else 0
        lease_term = item.lease_term if item.lease_term is not None else 0
        lease_type = item.lease_type

    context['buy_items'] = {
        'total': buy_total,
        'items': buy_items,
    }

    context['lease_items'] = {
        'total': lease_total,
        'items': lease_items,
        'lease_term': lease_term,
        'lease_type': lease_type
    }

    context['lease_items_4_nc'] = {
        'total': lease_total,
        'items': lease_items_4_nc,
        'lease_term': lease_term,
        'lease_type': lease_type
    }

    proposal_service_items = ProposalServiceItem.objects.filter(proposal=proposal)
    context['mps_items'] = {
        'count': proposal_service_items.count()
    }
    service_items = []
    service_items_4_nc = []
    for item in proposal_service_items:
        printer = Printer.objects.get(pk=item.printer.id)
        device_name = printer.short_model

        flat_rate = get_flat_rate(item)

        monthly_cost = 0
        if not item.is_non_network:
            monthly_cost = flat_rate
        else:
            monthly_cost = item.non_network_cost

        data = {
            'device_name': device_name,
            'monthly_cost': monthly_cost,
            'info': item,
            'device_count': item.number_printers_serviced
        }

        add_to_service_items_4_nc = True
        for lease_item in lease_items_4_nc:
          if lease_item.id == item.proposal_purchase_item_id:
            context['lease_items_4_nc']['total'] += monthly_cost
            lease_item.lease_payment += monthly_cost
            add_to_service_items_4_nc = False

        if add_to_service_items_4_nc:
          service_items_4_nc.append(data)

        service_items.append(data)

    context['service_items'] = service_items
    context['service_items_4_nc'] = service_items_4_nc

    if proposal.status == 'in-progress':
        signature_form = SignatureForm()

    elif proposal.status == 'proposal_accepted' and proposal.signature_image.name is not '':
        signature_form = settings.WEB_DOMAIN + proposal.signature_image.url
    else:
        signature_form = None
    
    context['form'] = signature_form

    return render(request, 'proposal/' + str(company.id) + '_nc.html', context)

def view_proposal_blended(request, proposal_id):
    proposal = Proposal.objects.get(pk=proposal_id)
    if request.method == 'POST':
        form = SignatureForm(request.POST)
        if form.is_valid():
            signature = form.cleaned_data.get('signature')
            if signature:
                signature_file_path = draw_signature(signature, as_file=True)

                path = os.path.join(settings.BASE_DIR, 'media/signature_image')
                if not os.path.exists(path):
                    os.makedirs(path)

                signature_image_path = copy2(signature_file_path, path)
                if os.path.exists(signature_file_path):
                    os.remove(signature_file_path)

                proposal.signature_image = signature_image_path.split('media')[-1]
                proposal.status = 'proposal_accepted'
                proposal.save()
    client = Client.objects.get(pk=proposal.client.id)
    sales_rep = MPS_User.objects.get(pk=proposal.sales_rep.id)
    company = Company.objects.get(pk=sales_rep.company.id)
    sales_rep_user = User.objects.get(pk=sales_rep.user.id)
    service_level = ServiceLevel.objects.get(pk=proposal.contract_service_level.id)
    account_settings = AccountSetting.objects.filter(company=company).order_by('-pk')[0]

    context = {
        'proposal': {
            'id': proposal_id,
            'term': proposal.term,
            'logo': account_settings.logo,
            'status': proposal.status,
            'response_time': service_level.responseTime,
            'service_type': proposal.contract_service_type,
            'create_date': proposal.create_date.date,
            'expiration_date': proposal.expiration_date.date,
            'signed_date': proposal.signed_date,
        },
        'client': {
            'name': client.organization_name,
            'contact': client.contact,
            'address': client.address,
            'city': client.city,
            'state': client.state,
            'zipcode': client.zipcode,
            'telephone': client.phone_number,
            'email': client.email,
        },
        'company': {
            'name': company.name,
            'telephone': company.phone_number,
        },
        'sales_rep': {
            'first_name': sales_rep_user.first_name,
            'last_name': sales_rep_user.last_name,
            'email': sales_rep_user.email,
        }
    }

    context['proposal_signed_date'] = proposal.signed_date or datetime.now().strftime('%d/%m/%Y')

    proposal_purchase_items = ProposalPurchaseItem.objects.filter(proposal=proposal)
    count = 0
    buy_items = []
    lease_items = []
    for item in proposal_purchase_items:
        count = count + item.number_printers_purchased
        if item.buy_or_lease == 'buy':
            buy_items.append(item)
            if not context.get('equipment_purchase'):
                context['equipment_purchase'] = True
        elif item.buy_or_lease == 'lease':
            lease_items.append(item)
            if not context.get('equipment_lease'):
                context['equipment_lease'] = True
        elif item.buy_or_lease == 'rent':
            lease_items.append(item)
            if not context.get('equipment_rent'):
                context['equipment_rent'] = True

    buy_total = 0
    for item in buy_items:
        buy_total = buy_total + item.proposed_cost
        long_model = item.long_model if item.long_model is not None else 0
        lease_term = item.lease_term if item.lease_term is not None else 0
        lease_type = 0

    lease_total = 0
    lease_term = 0
    lease_type = 0
    for item in lease_items:
        lease_total = lease_total + item.lease_payment
        long_model = item.long_model if item.long_model is not None else 0
        lease_term = item.lease_term if item.lease_term is not None else 0
        lease_type = item.lease_type

    context['buy_items'] = {
        'total': buy_total,
        'items': buy_items,
    }

    context['lease_items'] = {
        'total': lease_total,
        'items': lease_items,
        'lease_term': lease_term,
        'lease_type': lease_type
    }

    proposal_service_items = ProposalServiceItem.objects.filter(proposal=proposal)
    network_devices = []
    non_network_devices = []
    for item in proposal_service_items:
        if item.is_non_network:
            printer = Printer.objects.get(pk=item.printer.id)
            device_name = printer.short_model
            data = {
                'device_name': device_name,
                'non_network_cost': item.non_network_cost
            }
            non_network_devices.append(data)
        else:
            network_devices.append(item)


    mono_items = []
    mono_on_color_items = []
    color_items = []
    for item in network_devices:
        printer = Printer.objects.get(pk=item.printer.id)
        device_name = printer.short_model
        if printer.cyan_toner == False:
            if item.total_mono_pages > 0:
                data = {
                    'device_name': device_name,
                    'device_count': item.number_printers_serviced
                }
                mono_items.append(data)
                
                if item.proposal_purchase_item and item.proposal_purchase_item.buy_or_lease == 'buy':
                    if not context.get('mono__buy'):
                        context['mono__buy'] = 'buy'

                if item.proposal_purchase_item and item.proposal_purchase_item.buy_or_lease == 'rent':
                    if not context.get('mono__lease'):
                        context['mono__lease'] = 'rent'
                
                if item.proposal_purchase_item and item.proposal_purchase_item.buy_or_lease == 'lease':
                    if not context.get('mono__lease'):
                        context['mono__lease'] = 'lease'

                    if item.proposal_purchase_item.lease_type == 'fmv':
                        if not context.get('mono__lease_type__fmv'):
                            context['mono__lease_type__fmv'] = 'fmv'
                    if item.proposal_purchase_item.lease_type == 'Fair Market Value':
                        if not context.get('mono__lease_type__fmv'):
                            context['mono__lease_type__fmv'] = 'Fair Market Value'
                    if item.proposal_purchase_item.lease_type == 'Fair Market Value, New Lease, New Equipment Only':
                        if not context.get('mono__lease_type__fmv'):
                            context['mono__lease_type__fmv'] = 'Fair Market Value, New Lease, New Equipment Only'
                    if item.proposal_purchase_item.lease_type == 'True Rental, Customer FMV Rate':
                        if not context.get('mono__lease_type__fmv'):
                            context['mono__lease_type__fmv'] = 'True Rental, Customer FMV Rate'
                    if item.proposal_purchase_item.lease_type == 'Knock-Out, Fair Market Value':
                        if not context.get('mono__lease_type__fmv'):
                            context['mono__lease_type__fmv'] = 'Knock-Out, Fair Market Value'
                    if item.proposal_purchase_item.lease_type == 'FMV, 90 Day Deferred':
                        if not context.get('mono__lease_type__fmv'):
                            context['mono__lease_type__fmv'] = 'FMV, 90 Day Deferred'
                    if item.proposal_purchase_item.lease_type == 'FMV, 90 Day Deferred, Knock-Out':
                        if not context.get('mono__lease_type__fmv'):
                            context['mono__lease_type__fmv'] = 'FMV, 90 Day Deferred, Knock-Out'
                            
                    if item.proposal_purchase_item.lease_type == 'buyout':
                        if not context.get('mono__lease_type__buyout'):
                            context['mono__lease_type__buyout'] = 'buyout'
                    if item.proposal_purchase_item.lease_type == '$1 Buyout':
                        if not context.get('mono__lease_type__buyout'):
                            context['mono__lease_type__buyout'] = '$1 Buyout'
                    if item.proposal_purchase_item.lease_type == '$1 Buyout, 90 Day Deferred':
                        if not context.get('mono__lease_type__buyout'):
                            context['mono__lease_type__buyout'] = '$1 Buyout, 90 Day Deferred'
        else:
            if item.total_mono_pages > 0:
                data = {
                    'device_name': device_name,
                    'device_count': item.number_printers_serviced
                }
                mono_on_color_items.append(data)

                if item.proposal_purchase_item and item.proposal_purchase_item.buy_or_lease == 'buy':
                    if not context.get('mono_on_color__buy'):
                        context['mono_on_color__buy'] = 'buy'

                if item.proposal_purchase_item and item.proposal_purchase_item.buy_or_lease == 'rent':
                    if not context.get('mono_on_color__lease'):
                        context['mono_on_color__lease'] = 'rent'

                if item.proposal_purchase_item and item.proposal_purchase_item.buy_or_lease == 'lease':
                    if not context.get('mono_on_color__lease'):
                        context['mono_on_color__lease'] = 'lease'

                    if item.proposal_purchase_item.lease_type == 'fmv':
                        if not context.get('mono_on_color__lease_type__fmv'):
                            context['mono_on_color__lease_type__fmv'] = 'fmv'
                    if item.proposal_purchase_item.lease_type == 'Fair Market Value':
                        if not context.get('mono_on_color__lease_type__fmv'):
                            context['mono_on_color__lease_type__fmv'] = 'Fair Market Value'
                    if item.proposal_purchase_item.lease_type == 'Fair Market Value, New Lease, New Equipment Only':
                        if not context.get('mono_on_color__lease_type__fmv'):
                            context['mono_on_color__lease_type__fmv'] = 'Fair Market Value, New Lease, New Equipment Only'
                    if item.proposal_purchase_item.lease_type == 'True Rental, Customer FMV Rate':
                        if not context.get('mono_on_color__lease_type__fmv'):
                            context['mono_on_color__lease_type__fmv'] = 'True Rental, Customer FMV Rate'
                    if item.proposal_purchase_item.lease_type == 'Knock-Out, Fair Market Value':
                        if not context.get('mono_on_color__lease_type__fmv'):
                            context['mono_on_color__lease_type__fmv'] = 'Knock-Out, Fair Market Value'
                    if item.proposal_purchase_item.lease_type == 'FMV, 90 Day Deferred':
                        if not context.get('mono_on_color__lease_type__fmv'):
                            context['mono_on_color__lease_type__fmv'] = 'FMV, 90 Day Deferred'
                    if item.proposal_purchase_item.lease_type == 'FMV, 90 Day Deferred, Knock-Out':
                        if not context.get('mono_on_color__lease_type__fmv'):
                            context['mono_on_color__lease_type__fmv'] = 'FMV, 90 Day Deferred, Knock-Out'

                    if item.proposal_purchase_item.lease_type == 'buyout':
                        if not context.get('mono_on_color__lease_type__buyout'):
                            context['mono_on_color__lease_type__buyout'] = 'buyout'
                    if item.proposal_purchase_item.lease_type == '$1 Buyout':
                        if not context.get('mono_on_color__lease_type__buyout'):
                            context['mono_on_color__lease_type__buyout'] = '$1 Buyout'
                    if item.proposal_purchase_item.lease_type == '$1 Buyout, 90 Day Deferred':
                        if not context.get('mono_on_color__lease_type__buyout'):
                            context['mono_on_color__lease_type__buyout'] = '$1 Buyout, 90 Day Deferred'

            if item.total_color_pages > 0:
                data = {
                    'device_name': device_name,
                    'device_count': item.number_printers_serviced
                }
                color_items.append(data)

                if item.proposal_purchase_item and item.proposal_purchase_item.buy_or_lease == 'buy':
                    if not context.get('color__buy'):
                        context['color__buy'] = 'buy'

                if item.proposal_purchase_item and item.proposal_purchase_item.buy_or_lease == 'rent':
                    if not context.get('color__lease'):
                        context['color__lease'] = 'rent'

                if item.proposal_purchase_item and item.proposal_purchase_item.buy_or_lease == 'lease':
                    if not context.get('color__lease'):
                        context['color__lease'] = 'lease'

                    if item.proposal_purchase_item.lease_type == 'fmv':
                        if not context.get('color__lease_type__fmv'):
                            context['color__lease_type__fmv'] = 'fmv'
                    if item.proposal_purchase_item.lease_type == 'Fair Market Value':
                        if not context.get('color__lease_type__fmv'):
                            context['color__lease_type__fmv'] = 'Fair Market Value'
                    if item.proposal_purchase_item.lease_type == 'Fair Market Value, New Lease, New Equipment Only':
                        if not context.get('color__lease_type__fmv'):
                            context['color__lease_type__fmv'] = 'Fair Market Value, New Lease, New Equipment Only'
                    if item.proposal_purchase_item.lease_type == 'True Rental, Customer FMV Rate':
                        if not context.get('color__lease_type__fmv'):
                            context['color__lease_type__fmv'] = 'True Rental, Customer FMV Rate'
                    if item.proposal_purchase_item.lease_type == 'Knock-Out, Fair Market Value':
                        if not context.get('color__lease_type__fmv'):
                            context['color__lease_type__fmv'] = 'Knock-Out, Fair Market Value'
                    if item.proposal_purchase_item.lease_type == 'FMV, 90 Day Deferred':
                        if not context.get('color__lease_type__fmv'):
                            context['color__lease_type__fmv'] = 'FMV, 90 Day Deferred'
                    if item.proposal_purchase_item.lease_type == 'FMV, 90 Day Deferred, Knock-Out':
                        if not context.get('color__lease_type__fmv'):
                            context['color__lease_type__fmv'] = 'FMV, 90 Day Deferred, Knock-Out'

                    if item.proposal_purchase_item.lease_type == 'buyout':
                        if not context.get('color__lease_type__buyout'):
                            context['color__lease_type__buyout'] = 'buyout'
                    if item.proposal_purchase_item.lease_type == '$1 Buyout':
                        if not context.get('color__lease_type__buyout'):
                            context['color__lease_type__buyout'] = '$1 Buyout'
                    if item.proposal_purchase_item.lease_type == '$1 Buyout, 90 Day Deferred':
                        if not context.get('color__lease_type__buyout'):
                            context['color__lease_type__buyout'] = '$1 Buyout, 90 Day Deferred'

    context['mono'] = {}
    if len(mono_items) > 0:
        cpp_mono = proposal.bln_proposed_price_mono if (proposal.bln_proposed_price_mono or 0) > 0 else proposal.bln_rcmd_price_mono
        context['mono'] = {
            'monthly_cost': proposal.bln_base_rate_mono,
            'cpp_mono': cpp_mono,
            'base_volume_mono': proposal.bln_base_volume_mono,
            'items': mono_items
        }

    context['mono_on_color'] = {}
    if len(mono_on_color_items) > 0:
        cpp_mono_on_color = proposal.bln_proposed_price_mono_on_color if (proposal.bln_proposed_price_mono_on_color or 0) > 0 else proposal.bln_rcmd_price_mono_on_color
        context['mono_on_color'] = {
            'monthly_cost': proposal.bln_base_rate_mono_on_color,
            'cpp_mono_on_color': cpp_mono_on_color,
            'base_volume_mono_on_color': proposal.bln_base_volume_mono_on_color,
            'items': mono_on_color_items
        }

    context['color'] = {}
    if len(color_items) > 0:
        cpp_color = proposal.bln_proposed_price_color if (proposal.bln_proposed_price_color or 0) > 0 else proposal.bln_rcmd_price_color
        context['color'] = {
            'monthly_cost': proposal.bln_base_rate_color,
            'cpp_color': cpp_color,
            'base_volume_color': proposal.bln_base_volume_color,
            'items': color_items
        }

    context['non_network_devices'] = non_network_devices

    if proposal.status == 'in-progress':
        signature_form = SignatureForm()

    elif proposal.status == 'proposal_accepted' and proposal.signature_image.name is not '':
        signature_form = settings.WEB_DOMAIN + proposal.signature_image.url
    else:
        signature_form = None
    
    context['form'] = signature_form

    return render(request, 'proposal/' + str(company.id) + '_blended.html', context)

def view_proposal_tiered(request, proposal_id):
    proposal = Proposal.objects.get(pk=proposal_id)
    if request.method == 'POST':
        form = SignatureForm(request.POST)
        if form.is_valid():
            signature = form.cleaned_data.get('signature')
            if signature:
                signature_file_path = draw_signature(signature, as_file=True)

                path = os.path.join(settings.BASE_DIR, 'media/signature_image')
                if not os.path.exists(path):
                    os.makedirs(path)

                signature_image_path = copy2(signature_file_path, path)
                if os.path.exists(signature_file_path):
                    os.remove(signature_file_path)

                proposal.signature_image = signature_image_path.split('media')[-1]
                proposal.status = 'proposal_accepted'
                proposal.save()
    client = Client.objects.get(pk=proposal.client.id)
    sales_rep = MPS_User.objects.get(pk=proposal.sales_rep.id)
    company = Company.objects.get(pk=sales_rep.company.id)
    sales_rep_user = User.objects.get(pk=sales_rep.user.id)
    service_level = ServiceLevel.objects.get(pk=proposal.contract_service_level.id)
    account_settings = AccountSetting.objects.filter(company=company).order_by('-pk')[0]

    context = {
        'proposal': {
            'id': proposal_id,
            'logo': account_settings.logo,
            'term': proposal.term,
            'status': proposal.status,
            'response_time': service_level.responseTime,
            'service_type': proposal.contract_service_type,
            'create_date': proposal.create_date.date,
            'expiration_date': proposal.expiration_date.date,
            'signed_date': proposal.signed_date,
        },
        'client': {
            'name': client.organization_name,
            'contact': client.contact,
            'address': client.address,
            'city': client.city,
            'state': client.state,
            'zipcode': client.zipcode,
            'telephone': client.phone_number,
            'email': client.email,
        },
        'company': {
            'name': company.name,
            'telephone': company.phone_number,
        },
        'sales_rep': {
            'first_name': sales_rep_user.first_name,
            'last_name': sales_rep_user.last_name,
            'email': sales_rep_user.email,
        }
    }

    context['proposal_signed_date'] = proposal.signed_date or datetime.now().strftime('%d/%m/%Y')

    proposal_purchase_items = ProposalPurchaseItem.objects.filter(proposal=proposal)
    count = 0
    buy_items = []
    lease_items = []
    for item in proposal_purchase_items:
        count = count + item.number_printers_purchased
        if item.buy_or_lease == 'buy':
            buy_items.append(item)
        elif item.buy_or_lease == 'lease':
            lease_items.append(item)
        elif item.buy_or_lease == 'rent':
            lease_items.append(item)

    buy_total = 0
    for item in buy_items:
        buy_total = buy_total + item.proposed_cost

    lease_total = 0
    for item in lease_items:
        lease_total = lease_total + item.lease_payment

    context['buy_items'] = {
        'total': buy_total,
        'items': buy_items
    }

    context['lease_items'] = {
        'total': lease_total,
        'items': lease_items
    }

    proposal_service_items = ProposalServiceItem.objects.filter(proposal=proposal)
    network_devices = []
    non_network_devices = []
    for item in proposal_service_items:
        if item.is_non_network:
            printer = Printer.objects.get(pk=item.printer.id)
            device_name = printer.short_model
            data = {
                'device_name': device_name,
                'non_network_cost': item.non_network_cost
            }
            non_network_devices.append(data)
        else:
            network_devices.append(item)

    bw1_items = []
    bw2_items = []
    bw3_items = []
    bw4_items = []
    color1_items = []
    color2_items = []
    color3_items = []
    for item in network_devices:
        printer = Printer.objects.get(pk=item.printer.id)
        device_name = printer.short_model
        if item.tier_level_mono:
            data = {
                'device_name': device_name,
                'device_count': item.number_printers_serviced,
                'cost': item.base_rate_mono,
                'volume': item.base_volume_mono
            }
            if item.tier_level_mono == 'bw1':
                bw1_items.append(data)
            elif item.tier_level_mono == 'bw2':
                bw2_items.append(data)
            elif item.tier_level_mono == 'bw3':
                bw3_items.append(data)
            elif item.tier_level_mono == 'bw4':
                bw4_items.append(data)

        if item.tier_level_color:
            data = {
                'device_name': device_name,
                'device_count': item.number_printers_serviced,
                'cost': item.base_rate_color,
                'volume': item.base_volume_color
            }
            if item.tier_level_color == 'color1':
                color1_items.append(data)
            elif item.tier_level_color == 'color2':
                color2_items.append(data)
            elif item.tier_level_color == 'color3':
                color3_items.append(data)

    tiered_values = TieredValue.objects.get(proposal=proposal)
    context['mono1'] = {}
    if len(bw1_items) > 0:
        cpp_mono = tiered_values.bw1_proposed_cpp if (tiered_values.bw1_proposed_cpp or 0) > 0 else tiered_values.bw1_overage_cpp

        monthly_cost = 0
        base_volume_mono = 0
        for item in bw1_items:
            monthly_cost = monthly_cost + item['cost']
            base_volume_mono = base_volume_mono + item['volume']

        context['mono1'] = {
            'monthly_cost': monthly_cost,
            'cpp_mono': cpp_mono,
            'base_volume_mono': base_volume_mono,
            'items': bw1_items
        }

    context['mono2'] = {}
    if len(bw2_items) > 0:
        cpp_mono = tiered_values.bw2_proposed_cpp if (tiered_values.bw2_proposed_cpp or 0) > 0 else tiered_values.bw2_overage_cpp

        monthly_cost = 0
        base_volume_mono = 0
        for item in bw2_items:
            monthly_cost = monthly_cost + item['cost']
            base_volume_mono = base_volume_mono + item['volume']

        context['mono2'] = {
            'monthly_cost': monthly_cost,
            'cpp_mono': cpp_mono,
            'base_volume_mono': base_volume_mono,
            'items': bw2_items
        }

    context['mono3'] = {}
    if len(bw3_items) > 0:
        cpp_mono = tiered_values.bw3_proposed_cpp if (tiered_values.bw3_proposed_cpp or 0) > 0 else tiered_values.bw3_overage_cpp

        monthly_cost = 0
        base_volume_mono = 0
        for item in bw3_items:
            monthly_cost = monthly_cost + item['cost']
            base_volume_mono = base_volume_mono + item['volume']

        context['mono3'] = {
            'monthly_cost': monthly_cost,
            'cpp_mono': cpp_mono,
            'base_volume_mono': base_volume_mono,
            'items': bw3_items
        }

    context['mono4'] = {}
    if len(bw4_items) > 0:
        cpp_mono = tiered_values.bw4_proposed_cpp if (tiered_values.bw4_proposed_cpp or 0) > 0 else tiered_values.bw4_overage_cpp

        monthly_cost = 0
        base_volume_mono = 0
        for item in bw4_items:
            monthly_cost = monthly_cost + item['cost']
            base_volume_mono = base_volume_mono + item['volume']

        context['mono4'] = {
            'monthly_cost': monthly_cost,
            'cpp_mono': cpp_mono,
            'base_volume_mono': base_volume_mono,
            'items': bw4_items
        }

    context['color1'] = {}
    if len(color1_items) > 0:
        cpp_color = tiered_values.color1_proposed_cpp if (tiered_values.color1_proposed_cpp or 0) > 0 else tiered_values.color1_overage_cpp

        monthly_cost = 0
        base_volume_color = 0
        for item in color1_items:
            monthly_cost = monthly_cost + item['cost']
            base_volume_color = base_volume_color + item['volume']

        context['color1'] = {
            'monthly_cost': monthly_cost,
            'cpp_color': cpp_color,
            'base_volume_color': base_volume_color,
            'items': color1_items
        }

    context['color2'] = {}
    if len(color2_items) > 0:
        cpp_color = tiered_values.color2_proposed_cpp if (tiered_values.color2_proposed_cpp or 0) > 0 else tiered_values.color2_overage_cpp

        monthly_cost = 0
        base_volume_color = 0
        for item in color2_items:
            monthly_cost = monthly_cost + item['cost']
            base_volume_color = base_volume_color + item['volume']

        context['color2'] = {
            'monthly_cost': monthly_cost,
            'cpp_color': cpp_color,
            'base_volume_color': base_volume_color,
            'items': color2_items
        }

    context['color3'] = {}
    if len(color3_items) > 0:
        cpp_color = tiered_values.color3_proposed_cpp if (tiered_values.color3_proposed_cpp or 0) > 0 else tiered_values.color3_overage_cpp

        monthly_cost = 0
        base_volume_color = 0
        for item in color3_items:
            monthly_cost = monthly_cost + item['cost']
            base_volume_color = base_volume_color + item['volume']

        context['color3'] = {
            'monthly_cost': monthly_cost,
            'cpp_color': cpp_color,
            'base_volume_color': base_volume_color,
            'items': color3_items
        }

    context['non_network_devices'] = non_network_devices

    if proposal.status == 'in-progress':
        signature_form = SignatureForm()

    elif proposal.status == 'proposal_accepted' and proposal.signature_image.name is not '':
        signature_form = settings.WEB_DOMAIN + proposal.signature_image.url
    else:
        signature_form = None
    
    context['form'] = signature_form

    return render(request, 'proposal/' + str(company.id) + '_tiered.html', context)

def view_proposal_ppc(request, proposal_id):
    proposal = Proposal.objects.get(pk=proposal_id)
    if request.method == 'POST':
        form = SignatureForm(request.POST)
        if form.is_valid():
            signature = form.cleaned_data.get('signature')
            if signature:
                signature_file_path = draw_signature(signature, as_file=True)

                path = os.path.join(settings.BASE_DIR, 'media/signature_image')
                if not os.path.exists(path):
                    os.makedirs(path)

                signature_image_path = copy2(signature_file_path, path)
                if os.path.exists(signature_file_path):
                    os.remove(signature_file_path)

                proposal.signature_image = signature_image_path.split('media')[-1]
                proposal.status = 'proposal_accepted'
                proposal.save()
    client = Client.objects.get(pk=proposal.client.id)
    sales_rep = MPS_User.objects.get(pk=proposal.sales_rep.id)
    company = Company.objects.get(pk=sales_rep.company.id)
    sales_rep_user = User.objects.get(pk=sales_rep.user.id)
    service_level = ServiceLevel.objects.get(pk=proposal.contract_service_level.id)
    account_settings = AccountSetting.objects.filter(company=company).order_by('-pk')[0]

    context = {
        'proposal': {
            'id': proposal_id,
            'logo': account_settings.logo,
            'term': proposal.term,
            'status': proposal.status,
            'response_time': service_level.responseTime,
            'service_type': proposal.contract_service_type,
            'create_date': proposal.create_date.date,
            'expiration_date': proposal.expiration_date.date,
            'signed_date': proposal.signed_date,
        },
        'client': {
            'name': client.organization_name,
            'contact': client.contact,
            'address': client.address,
            'city': client.city,
            'state': client.state,
            'zipcode': client.zipcode,
            'telephone': client.phone_number,
            'email': client.email,
        },
        'company': {
            'name': company.name,
            'telephone': company.phone_number,
        },
        'sales_rep': {
            'first_name': sales_rep_user.first_name,
            'last_name': sales_rep_user.last_name,
            'email': sales_rep_user.email,
        }
    }

    context['proposal_signed_date'] = proposal.signed_date or datetime.now().strftime('%d/%m/%Y')

    proposal_purchase_items = ProposalPurchaseItem.objects.filter(proposal=proposal)
    count = 0
    buy_items = []
    lease_items = []
    for item in proposal_purchase_items:
        count = count + item.number_printers_purchased
        if item.buy_or_lease == 'buy':
            buy_items.append(item)
        elif item.buy_or_lease == 'lease':
            lease_items.append(item)
        elif item.buy_or_lease == 'rent':
            lease_items.append(item)

    buy_total = 0
    for item in buy_items:
        buy_total = buy_total + item.proposed_cost

    lease_total = 0
    for item in lease_items:
        lease_total = lease_total + item.lease_payment

    context['buy_items'] = {
        'total': buy_total,
        'items': buy_items
    }

    context['lease_items'] = {
        'total': lease_total,
        'items': lease_items
    }

    proposal_service_items = ProposalServiceItem.objects.filter(proposal=proposal)
    service_total = 0
    service_items = []
    for item in proposal_service_items:
        printer = Printer.objects.get(pk=item.printer.id)
        device_name = printer.short_model
        ppc_mono = 0
        ppc_color = 0

        monthly_cost = 0
        if not item.is_non_network:
            monthly_cost = int(item.base_rate_mono or 0) + int(item.base_rate_color or 0)
            ppc_mono = item.proposed_cost_per_cartridge_mono if (item.proposed_cost_per_cartridge_mono or 0) > 0 else item.recommended_cost_per_cartridge_mono
            ppc_color = item.proposed_cost_per_cartridge_color if (item.proposed_cost_per_cartridge_color or 0) > 0 else item.recommended_cost_per_cartridge_color
        else:
            monthly_cost = item.non_network_cost

        x = {
            'device_name': device_name,
            'monthly_cost': monthly_cost,
            'ppc_mono': ppc_mono,
            'ppc_color': ppc_color,
            'info': item,
            'device_count': item.number_printers_serviced
        }
        service_items.append(x)

    context['service_items'] = service_items

    if proposal.status == 'in-progress':
        signature_form = SignatureForm()

    elif proposal.status == 'proposal_accepted' and proposal.signature_image.name is not '':
        signature_form = settings.WEB_DOMAIN + proposal.signature_image.url
    else:
        signature_form = None
    
    context['form'] = signature_form

    return render(request, 'proposal/' + str(company.id) + '_ppc.html', context)

def accept_proposal(request, proposal_id):
    proposal = Proposal.objects.get(pk=proposal_id)
    if request.method == 'POST' and proposal.status != 'proposal_accepted':
        form = SignatureForm(request.POST)
        if form.is_valid():
            signature = form.cleaned_data.get('signature')
            if signature:
                signature_file_path = draw_signature(signature, as_file=True)

                path = os.path.join(settings.BASE_DIR, 'media/signature_image')
                if not os.path.exists(path):
                    os.makedirs(path)

                signature_image_path = copy2(signature_file_path, path)
                if os.path.exists(signature_file_path):
                    os.remove(signature_file_path)

                proposal.signature_image = signature_image_path.split('media')[-1]
                proposal.status = 'proposal_accepted'
                proposal.is_approved = True
                proposal.signed_date = datetime.now()
                proposal.save()
    # if proposal.status != 'proposal_accepted':
    #     proposal.status = 'proposal_accepted'
    #     proposal.is_approved = True
    #     proposal.signed_date = datetime.now()
    #     proposal.save()


    return render(request, 'proposal/accepted.html')

def send_proposal(request, proposal_id):
    proposal = Proposal.objects.get(pk=proposal_id)
    client = Client.objects.get(pk=proposal.client.id)
    subject = client.organization_name + " Proposal"
    url = request.build_absolute_uri(reverse('mps:view_proposal_' + proposal.proposal_type, kwargs={'proposal_id': proposal_id}))
    message = url
    send_mail(subject, message, 'support@h4software.net', [client.email])
    return render(request, 'proposal/sent.html', {'proposal_id': proposal_id, 'proposal_url': url})

def send_proposal_to_me(request, proposal_id):
    proposal = Proposal.objects.get(pk=proposal_id)
    client = Client.objects.get(pk=proposal.client.id)
    subject = client.organization_name + " Proposal"
    url = request.build_absolute_uri(reverse('mps:view_proposal_' + proposal.proposal_type, kwargs={'proposal_id': proposal_id}))
    message = url
    sales_rep = MPS_User.objects.get(pk=proposal.sales_rep.id)
    send_mail(subject, message, 'support@h4software.net', [sales_rep.user.email])
    return render(request, 'proposal/sent.html', {'proposal_id': proposal_id, 'proposal_url': url})

def account_settings(request):
    if request.method == 'POST':
        account_settings = AccountSetting.objects.get(company=request.user.mps_user.company)
        form = AccountSettingForm(request.POST, request.FILES, instance=account_settings)
        if form.is_valid():
            logo = account_settings.logo
            co_branding_logo = account_settings.co_branding_logo
            account_settings.save(update_fields = list(request.FILES))
            return render(request, 'rep/account_settings.html', {'image_url': logo.url, 'co_branding_logo_url': co_branding_logo.url})
    else:
        form = AccountSettingForm()
    return render(request, 'rep/account_settings.html', {'form': form})


# view contract data - customer facing
def view_contract(request, proposal_id):
    proposal = Proposal.objects.get(pk=proposal_id)
    client = Client.objects.get(pk=proposal.client.id)
    sales_rep = MPS_User.objects.get(pk=proposal.sales_rep.id)
    company = Company.objects.get(pk=sales_rep.company.id)
    sales_rep_user = User.objects.get(pk=sales_rep.user.id)
    service_level = ServiceLevel.objects.get(pk=proposal.contract_service_level.id)
    account_settings = AccountSetting.objects.filter(company=company).order_by('-pk')[0]

    context = {
        'proposal': {
            'id': proposal_id,
            'logo': account_settings.logo,
            'term': proposal.term,
            'status': proposal.status,
            'response_time': service_level.responseTime,
            'service_type': proposal.contract_service_type,
            'create_date': proposal.create_date.date,
            'expiration_date': proposal.expiration_date.date,
            'proposal_type': proposal.proposal_type,
            'signed_date': proposal.signed_date,
        },
        'client': {
            'name': client.organization_name,
            'contact': client.contact,
            'address': client.address,
            'city': client.city,
            'state': client.state,
            'zipcode': client.zipcode,
            'phone_number': client.phone_number,
            'email': client.email,
        },
        'company': {
            'name': company.name,
            'address': company.address,
            'city': company.city,
            'state': company.state,
            'zipcode': company.zipcode,
        },
        'sales_rep': {
            'first_name': sales_rep_user.first_name,
            'last_name': sales_rep_user.last_name,
        }
    }

    proposal_service_items = ProposalServiceItem.objects.filter(proposal=proposal)

    service_items = []
    bw1_items = []
    bw2_items = []
    bw3_items = []
    bw4_items = []
    color1_items = []
    color2_items = []
    color3_items = []
    mono_items = []
    mono_on_color_items = []
    color_items = []

    for item in proposal_service_items:

        printer = Printer.objects.get(pk=item.printer.id)
        device_name = printer.short_model
        device_long_name = printer.display_description
        device_count = item.number_printers_serviced
        tier_level_mono = item.tier_level_mono
        tier_level_color = item.tier_level_color
        cpp_mono = 0
        cpp_color = 0
        ppc_mono = 0
        ppc_color = 0

        device_color = 0
        if not item.is_non_network and cpp_color > 0:
            device_color = 'Color 1'
        else:
            device_color = ''


        monthly_cost = 0
        if not item.is_non_network:
            monthly_cost = int(item.base_rate_mono or 0) + int(item.base_rate_color or 0)
            cpp_mono = item.proposed_cpp_mono if item.proposed_cpp_mono > 0 else item.rcmd_cpp_mono
            cpp_color = item.proposed_cpp_color if item.proposed_cpp_color > 0 else item.rcmd_cpp_color
            ppc_mono = item.proposed_cost_per_cartridge_mono if (item.proposed_cost_per_cartridge_mono or 0) > 0 else item.recommended_cost_per_cartridge_mono
            ppc_color = item.proposed_cost_per_cartridge_color if (item.proposed_cost_per_cartridge_color or 0) > 0 else item.recommended_cost_per_cartridge_color
        else:
            monthly_cost = item.non_network_cost

        flat_mono = 0
        flat_color = 0
        if (item.base_rate_mono or 0) == 0 and (item.proposed_cpp_mono or 0) == 0:
            flat_mono = (item.rcmd_cpp_mono or 0) * (item.total_mono_pages or 0)

        if (item.base_rate_mono or 0) == 0 and (item.proposed_cpp_mono or 0) > 0:
            flat_mono = item.proposed_cpp_mono * item.total_mono_pages

        if (item.base_rate_mono or 0) > 0 and (item.proposed_cpp_mono or 0) > 0:
            flat_mono = item.base_rate_mono + ((item.total_mono_pages - item.base_volume_mono) * item.proposed_cpp_mono)

        if (item.base_rate_mono or 0) > 0 and (item.proposed_cpp_mono or 0) == 0:
            flat_mono = item.base_rate_mono + ((item.total_mono_pages - item.base_volume_mono) * item.rcmd_cpp_mono)

        if (item.base_rate_color or 0) == 0 and (item.proposed_cpp_color or 0) == 0:
            flat_color = (item.rcmd_cpp_color or 0) * (item.total_color_pages or 0)

        if (item.base_rate_color or 0) == 0 and (item.proposed_cpp_color or 0) > 0:
            flat_color = item.proposed_cpp_color * item.total_color_pages

        if (item.base_rate_color or 0) > 0 and (item.proposed_cpp_color or 0) > 0:
            flat_color = item.base_rate_color + ((item.total_color_pages - item.base_volume_color) * item.proposed_cpp_color)

        if (item.base_rate_color or 0) > 0 and (item.proposed_cpp_color or 0) == 0:
            flat_color = item.base_rate_color + ((item.total_color_pages - item.base_volume_color) * item.rcmd_cpp_color)

        flat_rate = flat_mono + flat_color

        flat_price = 0
        if not item.is_non_network:
            flat_price = flat_rate
        else:
            flat_price = item.non_network_cost

        x = {
            'device_name': device_name,
            'device_long_name': device_long_name,
            'device_count': device_count,
            'tier_level_mono': tier_level_mono,
            'tier_level_color': tier_level_color,
            'monthly_cost': monthly_cost,
            'cpp_mono': cpp_mono,
            'cpp_color': cpp_color,
            'ppc_mono': ppc_mono,
            'ppc_color': ppc_color,
            'device_color': device_color,
            'flat_price': flat_price,
            'info': item
        }


        service_items.append(x)
        context['service_items'] = service_items

        tdata = {
            'cost': item.base_rate_mono,
            'volume': item.base_volume_mono
        }
        if item.tier_level_mono == 'bw1':
            bw1_items.append(tdata)
        elif item.tier_level_mono == 'bw2':
            bw2_items.append(tdata)
        elif item.tier_level_mono == 'bw3':
            bw3_items.append(tdata)
        elif item.tier_level_mono == 'bw4':
            bw4_items.append(tdata)

        if item.tier_level_color:
            tdata = {
                'cost': item.base_rate_color,
                'volume': item.base_volume_color
            }
            if item.tier_level_color == 'color1':
                color1_items.append(tdata)
            elif item.tier_level_color == 'color2':
                color2_items.append(tdata)
            elif item.tier_level_color == 'color3':
                color3_items.append(tdata)

        tiered_values = TieredValue.objects.get(proposal=proposal)
        if not item.is_non_network:
            if printer.cyan_toner == False:
                if item.total_mono_pages > 0:
                    data = {
                        'device_name': device_name,
                        'device_count': item.number_printers_serviced
                    }
                    mono_items.append(data)
            else:
                if item.total_mono_pages > 0:
                    data = {
                        'device_name': device_name,
                        'device_count': item.number_printers_serviced
                    }
                    mono_on_color_items.append(data)
                if item.total_color_pages > 0:
                    data = {
                        'device_name': device_name,
                        'device_count': item.number_printers_serviced
                    }
                    color_items.append(data)


        context['mono1'] = {}
        if len(bw1_items) > 0:
            tier_mono = tiered_values.bw1_proposed_cpp if (tiered_values.bw1_proposed_cpp or 0) > 0 else tiered_values.bw1_overage_cpp

            tier_cost = 0
            tier_volume_mono = 0
            for item in bw1_items:
                tier_cost = tier_cost + item['cost']
                tier_volume_mono = tier_volume_mono + item['volume']

            context['mono1'] = {
                'tier_cost': tier_cost,
                'tier_mono': tier_mono,
                'tier_volume_mono': tier_volume_mono,
            }

        context['mono2'] = {}
        if len(bw2_items) > 0:
            tier_mono = tiered_values.bw2_proposed_cpp if (tiered_values.bw2_proposed_cpp or 0) > 0 else tiered_values.bw2_overage_cpp

            tier_cost = 0
            tier_volume_mono = 0
            for item in bw2_items:
                tier_cost = tier_cost + item['cost']
                tier_volume_mono = tier_volume_mono + item['volume']

            context['mono2'] = {
                'tier_cost': tier_cost,
                'tier_mono': tier_mono,
                'tier_volume_mono': tier_volume_mono,
            }

        context['mono3'] = {}
        if len(bw3_items) > 0:
            tier_mono = tiered_values.bw3_proposed_cpp if (tiered_values.bw3_proposed_cpp or 0) > 0 else tiered_values.bw3_overage_cpp

            tier_cost = 0
            tier_volume_mono = 0
            for item in bw3_items:
                tier_cost = tier_cost + item['cost']
                tier_volume_mono = tier_volume_mono + item['volume']

            context['mono3'] = {
                'tier_cost': tier_cost,
                'tier_mono': tier_mono,
                'tier_volume_mono': tier_volume_mono,
            }

        context['mono4'] = {}
        if len(bw4_items) > 0:
            tier_mono = tiered_values.bw4_proposed_cpp if (tiered_values.bw4_proposed_cpp or 0) > 0 else tiered_values.bw4_overage_cpp

            tier_cost = 0
            tier_volume_mono = 0
            for item in bw4_items:
                tier_cost = tier_cost + item['cost']
                tier_volume_mono = tier_volume_mono + item['volume']

            context['mono4'] = {
                'tier_cost': tier_cost,
                'tier_mono': tier_mono,
                'tier_volume_mono': tier_volume_mono,
            }

        context['color1'] = {}
        if len(color1_items) > 0:
            tier_color = tiered_values.color1_proposed_cpp if (tiered_values.color1_proposed_cpp or 0) > 0 else tiered_values.color1_overage_cpp

            tier_cost = 0
            tier_volume_color = 0
            for item in color1_items:
                tier_cost = tier_cost + item['cost']
                tier_volume_color = tier_volume_color + item['volume']

            context['color1'] = {
                'tier_cost': tier_cost,
                'tier_color': tier_color,
                'tier_volume_color': tier_volume_color,
            }

        context['color2'] = {}
        if len(color2_items) > 0:
            tier_color = tiered_values.color2_proposed_cpp if (tiered_values.color2_proposed_cpp or 0) > 0 else tiered_values.color2_overage_cpp

            tier_cost = 0
            tier_volume_color = 0
            for item in color2_items:
                tier_cost = tier_cost + item['cost']
                tier_volume_color = tier_volume_color + item['volume']

            context['color2'] = {
                'tier_cost': tier_cost,
                'tier_color': tier_color,
                'tier_volume_color': tier_volume_color,
            }

        context['color3'] = {}
        if len(color3_items) > 0:
            tier_color = tiered_values.color3_proposed_cpp if (tiered_values.color3_proposed_cpp or 0) > 0 else tiered_values.color3_overage_cpp

            tier_cost = 0
            tier_volume_color = 0
            for item in color3_items:
                tier_cost = tier_cost + item['cost']
                tier_volume_mono = tier_volume_mono + item['volume']

            context['color3'] = {
                'tier_cost': tier_cost,
                'tier_color': tier_color,
                'tier_volume_color': tier_volume_color,
            }


        context['mono'] = {}
        if len(mono_items) > 0:
            blended_mono = proposal.bln_proposed_price_mono if proposal.bln_proposed_price_mono > 0 else proposal.bln_rcmd_price_mono
            context['mono'] = {
                'blended_mono_cost': proposal.bln_base_rate_mono,
                'blended_mono': blended_mono,
                'blended_volume_mono': proposal.bln_base_volume_mono,
                'items': mono_items
            }

        context['mono_on_color'] = {}
        if len(mono_on_color_items) > 0:
            blended_mono_on_color = proposal.bln_proposed_price_mono_on_color if proposal.bln_proposed_price_mono_on_color > 0 else proposal.bln_rcmd_price_mono_on_color
            context['mono_on_color'] = {
                'blended_mono_on_color_cost': proposal.bln_base_rate_mono_on_color,
                'blended_mono_on_color': blended_mono_on_color,
                'blended_volume_mono_on_color': proposal.bln_base_volume_mono_on_color,
                'items': mono_on_color_items
            }

        context['color'] = {}
        if len(color_items) > 0:
            blended_color = proposal.bln_proposed_price_color if proposal.bln_proposed_price_color > 0 else proposal.bln_rcmd_price_color
            context['color'] = {
                'blended_color_cost': proposal.bln_base_rate_color,
                'blended_color': blended_color,
                'blended_volume_color': proposal.bln_base_volume_color,
                'items': color_items
            }


    return render(request, 'contract/contract.html', context)

def consolidate_model_specifications(request): 
    '''
    consolidate the existing product specifications from the database.
    '''
    fields = [f.name for f in ModelSpecification._meta.get_fields()]
    
    csv_file = open(os.getcwd() + '/mps/static/csv-exports/modelspecs.csv', 'w')
    with csv_file:  
        writer = csv.DictWriter(csv_file, fieldnames=fields[1:])
        writer.writeheader()
        printers = PrinterCost.objects.all()

        for printer_cost in printers: 
            printer = Printer.objects.get(pk=printer_cost.printer_id)
            make = Make.objects.get(pk=printer.make_id)

            writer.writerow({
                'printer': printer_cost.printer_id, 
                'name': make.name,
                'c_bluetooth':'',
                'c_ethernet':'',
                'c_usb':'',
                'c_walk_up':'',
                'c_wifi':'',
                'duty_cycle_max':'',
                'duty_cycle_normal':'',
                'f_copy':'',
                'f_fax':'',
                'f_print':'',
                'f_scan':'',
                'mfg_model_number': printer_cost.product_id,
                'mfg_model_name':printer_cost.long_model,
                'o_adf_capacity':'',
                'o_borderless':'',
                'o_duplex':'',
                'o_duplex_scan':'',
                'o_staple':'',
                'o_touchscreen':'',
                'papersize_max':'',
                'papersize_supported':'',
                'ppm_color':'',
                'ppm_mono':'',
                'print_technology':'',
                'available':True})

    return HttpResponse('Request Sent!')

def build_model_specifications(request):
    '''
    import from csv modelspecifications data
    '''
    csv_file = open(os.getcwd() + '/mps/static/csv-exports/modelspecs.csv', 'r')
    from django.shortcuts import get_object_or_404
    with csv_file:
        def checkExists(pid):
            try: 
                Printer.objects.get(pk=pid)
                return True
            except: 
                return False

        reader = csv.DictReader(csv_file)
        # ModelSpecification.objects.bulk_create([ModelSpecification(
        #     printer=Printer.objects.get(pk=row['printer']),
        #     mfg_model_number=row['mfg_model_number'],
        #     mfg_model_name=row['mfg_model_name'],
        #     available=True) for row in reader if checkExists(row['printer'])], ignore_conflicts=True)

        # ModelSpecification.objects.bulk_create([ModelSpecification(
        #     printer=Printer.objects.get(pk=row['printer_id']), 
        #     # short_model=row['short_model'],
        #     name=row['name'], 
        #     # display_description=row['display_description'],
        #     # c_bluetooth=row['c_bluetooth'],
        #     # c_ethernet=row['c_ethernet'],
        #     # c_usb=row['c_usb'],
        #     # c_walk_up=row['c_walk_up'],
        #     # c_wifi=row['c_wifi'],
        #     duty_cycle_max=row['duty_cycle_max'],
        #     duty_cycle_normal=row['duty_cycle_normal'],
        #     # f_copy=row['f_copy'],
        #     # f_fax=row['f_fax'],
        #     f_print=eval(row['f_print']),
        #     # f_scan=row['f_scan'],
        #     mfg_model_number=row['mfg_model_number'],
        #     mfg_model_name=row['mfg_model_name'],
        #     o_adf_capacity=row['o_adf_capacity'],
        #     # o_borderless=row['o_borderless'],
        #     # o_duplex=row['o_duplex'],
        #     # o_duplex_scan=row['o_duplex_scan'],
        #     # o_staple=row['o_staple'],
        #     # o_touchscreen=row['o_touchscreen'],
        #     papersize_max=row['papersize_max'],
        #     papersize_supported=row['papersize_supported'],
        #     ppm_color=row['ppm_color'],
        #     ppm_mono=row['ppm_mono'],
        #     print_technology=row['print_technology'],
        #     available=True) for row in reader if checkExists(row['printer_id']) == True ], ignore_conflicts=True)

    return HttpResponse('Model Specifications updated')