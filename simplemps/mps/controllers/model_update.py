import json
from datetime import datetime
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.defaulttags import register
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict

from ..forms import UploadForm, ClientForm
from ..models import *
from .utils import convert_class_to_primitives


@login_required
@require_http_methods(['POST'])
def update_proposal_item_tier(request, proposal_id):
    data = json.loads(request.POST.get('data'))

    if 'bw' in data['tier']:
        ProposalServiceItem.objects.filter(id=data['printer_id']).update(tier_level_mono=data['tier'])
    elif 'color' in data['tier']:
        ProposalServiceItem.objects.filter(id=data['printer_id']).update(tier_level_color=data['tier'])

    return HttpResponse('Updated printer tier')


@login_required
@require_http_methods(['POST'])
def create_company(request):
    company_data_string = request.POST.get('company_data')
    company_data = json.loads(company_data_string)
    company = Company(**company_data)
    company.save()
    assumption = ManagementAssumption(company=company)
    assumption.save()
    return HttpResponse("Successfully imported company!")

# @login_required
@require_http_methods(['POST'])
def create_proposal_network_device(request, proposal_id):
    service_info = json.loads(request.POST.get('proposed_service'))
    printer = Printer.objects.get(id=service_info['printer'])
    service_info['printer'] = printer
    service_info['proposal'] = Proposal.objects.get(id=proposal_id)
    if(request.user.is_anonymous):
        mps_user = MPS_User.objects.get(pk=service_info['proposal'].sales_rep_id)
        user = User.objects.get(pk=mps_user.user_id)
        
        assumption = ManagementAssumption.objects.get(company=mps_user.company)
    else:
        assumption = ManagementAssumption.objects.get(company=request.user.mps_user.company)

    is_non_network = service_info['is_non_network']
    if not is_non_network:
        service_info['non_network_cost'] = None
        cpp_mono = float(service_info['proposed_cpp_mono']) if service_info['proposed_cpp_mono'] != 0 else float(service_info['rcmd_cpp_mono'])
        cpp_color = float(service_info['proposed_cpp_color']) if service_info['proposed_cpp_color'] != 0 else float(service_info['rcmd_cpp_color'])

    if is_non_network:
        tier_level_mono = None
    elif cpp_mono <= assumption.bw1_cpp:
        tier_level_mono = 'bw1'
    elif cpp_mono <= assumption.bw2_cpp:
        tier_level_mono = 'bw2'
    elif cpp_mono <= assumption.bw3_cpp:
        tier_level_mono = 'bw3'
    else:
        tier_level_mono = 'bw4'

    if not printer.is_color_device or is_non_network:
        tier_level_color = None
    elif cpp_color <= assumption.color1_cpp:
        tier_level_color = 'color1'
    elif cpp_color <= assumption.color2_cpp:
        tier_level_color = 'color2'
    else:
        tier_level_color = 'color3'

    service_info['tier_level_mono'] = tier_level_mono
    service_info['tier_level_color'] = tier_level_color

    new_printer_item = ProposalServiceItem(**service_info)
    if not is_non_network:
        new_printer_item.set_recommended_mono_cost_per_cartridge()
        new_printer_item.set_recommended_color_cost_per_cartridge()
    new_printer_item.full_clean()
    new_printer_item.save()

    purchase_info = json.loads(request.POST.get('proposed_purchase'))
    # was the semi-colon a bug?  changed (GEL 2019-11-20)
    #new_purchase_item_id = '';
    new_purchase_item_id = ''
    if purchase_info:
        purchase_info['printer'] = service_info['printer']
        purchase_info['proposal'] = service_info['proposal']

        new_purchase_item = ProposalPurchaseItem(**purchase_info)
        # new_purchase_item.set_recommended_mono_cost_per_cartridge()
        # new_purchase_item.set_recommended_color_cost_per_cartridge()
        new_purchase_item.full_clean()
        new_purchase_item.save()
        new_printer_item.proposal_purchase_item = new_purchase_item
        new_purchase_item_id = new_purchase_item.id
        new_printer_item.save()

    return HttpResponse(json.dumps(
        {
            'service_item_id': new_printer_item.id,
            'purchase_item_id': new_purchase_item_id,
            'mono_tier': tier_level_mono,
            'color_tier': tier_level_color
        }
    ))

@login_required
@require_http_methods(['POST'])
def create_proposal_tco_device(request, proposal_id):
    service_info = json.loads(request.POST.get('proposed_service'))
    assumption = ManagementAssumption.objects.get(company=request.user.mps_user.company)

    proposal = Proposal.objects.get(id=proposal_id)

    tco_item = ProposalTCOItem(
      proposalTCO = ProposalTCO.objects.get(proposal=proposal),
      printer = Printer.objects.get(id=service_info['printer']),
      number_printers_serviced = service_info['number_printers_serviced'],
      total_mono_pages = service_info['total_mono_pages'],
      total_color_pages = service_info['total_color_pages'],
      current_cpp_mono = service_info['current_cpp_mono'],
      current_cpp_color = service_info['current_cpp_color'],
      mono_toner_price = 0,
      color_toner_price = 0,
      service_cost = 0,
      base_volume_mono = service_info["base_volume_mono"],
      base_volume_color = service_info["base_volume_color"],
      base_rate_mono = service_info["base_rate_mono"],
      base_rate_color = service_info["base_rate_color"],
      monthly_lease_payment = service_info["monthly_lease_payment"]
    )

    tco_item.save()
    return JsonResponse({"device": model_to_dict(tco_item)})

@login_required
@require_http_methods(['POST'])
def update_tco_calculations(request, proposal_id):
  proposal = Proposal.objects.get(id=proposal_id)

  mps_price = request.POST.get('mps_price')
  monthly_lease = request.POST.get('monthly_lease')

  proposal.mps_price = mps_price
  proposal.monthly_lease = monthly_lease
  proposal.save()

  return HttpResponse({'success': 'success'})

@login_required
@require_http_methods(['POST'])
def update_tco_device(request, proposal_id):
  device_updates = json.loads(request.body)["device"]
  device = ProposalTCOItem.objects.filter(id=device_updates["id"])
  device_updates['proposalserviceitem_id'] = None
  device_updates['current_cpp_mono'] =  Decimal(device_updates['current_cpp_mono']) if device_updates['current_cpp_mono'] else 0.00
  device_updates['current_cpp_color'] = Decimal(device_updates['current_cpp_color']) if device_updates['current_cpp_color'] else 0.00
  device_updates['base_rate_mono'] = Decimal(device_updates['base_rate_mono']) if device_updates['base_rate_mono'] else 0.00
  device_updates['base_rate_color'] = Decimal(device_updates['base_rate_color']) if device_updates['base_rate_color'] else 0.00
  device.update(**device_updates)

  return HttpResponse({'success': 'success'})

@login_required
@require_http_methods(['POST'])
def save_blended_proposal_data(request, proposal_id):
    blended_proposal_data = json.loads(request.POST.get('blended_proposal_data'))
    proposal = Proposal.objects.get(id=proposal_id)
    proposal.bln_base_volume_mono = (blended_proposal_data['bln_base_volume_mono'] or 0)
    proposal.bln_base_rate_mono = (blended_proposal_data['bln_base_rate_mono'] or 0)
    proposal.bln_rcmd_price_mono = (blended_proposal_data['bln_rcmd_price_mono'] or 0)
    proposal.bln_proposed_price_mono = (blended_proposal_data['bln_proposed_price_mono'] or 0)
    proposal.bln_base_volume_mono_on_color = (blended_proposal_data['bln_base_volume_mono_on_color'] or 0)
    proposal.bln_base_rate_mono_on_color = (blended_proposal_data['bln_base_rate_mono_on_color'] or 0)
    proposal.bln_rcmd_price_mono_on_color = (blended_proposal_data['bln_rcmd_price_mono_on_color'] or 0)
    proposal.bln_proposed_price_mono_on_color = (blended_proposal_data['bln_proposed_price_mono_on_color'] or 0)
    proposal.bln_base_volume_color = (blended_proposal_data['bln_base_volume_color'] or 0)
    proposal.bln_base_rate_color = (blended_proposal_data['bln_base_rate_color'] or 0)
    proposal.bln_rcmd_price_color = (blended_proposal_data['bln_rcmd_price_color'] or 0)
    proposal.bln_proposed_price_color = (blended_proposal_data['bln_proposed_price_color'] or 0)
    proposal.save()
    return HttpResponse({'success': 'success'})

@login_required
@require_http_methods(['POST'])
def save_tiered_proposal_data(request, proposal_id):
    tiered_proposal_data = json.loads(request.POST.get('tiered_proposal_data'))
    proposal = Proposal.objects.get(id=proposal_id)
    tiered_values = TieredValue.objects.get(proposal=proposal)
    tiered_values.bw1_overage_cpp = tiered_proposal_data['bw1_overage_cpp']
    tiered_values.bw2_overage_cpp = tiered_proposal_data['bw2_overage_cpp']
    tiered_values.bw3_overage_cpp = tiered_proposal_data['bw3_overage_cpp']
    tiered_values.bw4_overage_cpp = tiered_proposal_data['bw4_overage_cpp']
    tiered_values.color1_overage_cpp = tiered_proposal_data['color1_overage_cpp']
    tiered_values.color2_overage_cpp = tiered_proposal_data['color2_overage_cpp']
    tiered_values.color3_overage_cpp = tiered_proposal_data['color3_overage_cpp']
    tiered_values.save()
    return HttpResponse({'success': 'success'})

# @login_required
@require_http_methods(['POST'])
def remove_proposal_network_device(request, proposal_id):
    device = ProposalServiceItem.objects.get(id=request.POST['id'], proposal=proposal_id)
    if device.proposal_purchase_item:
        device.proposal_purchase_item.delete()
    else:
        device.delete()
    return HttpResponse(status=200)

@login_required
@require_http_methods(['POST'])
def remove_proposal_tco_device(request, proposal_id):
    device = ProposalTCOItem.objects.get(id=request.POST['id'])
    device.delete()
    return HttpResponse(status=200)


#TODO THIS NEEDS TO BE FIXED
#TODO: 'create'
@login_required
@require_http_methods(['POST'])
def create_client(request):
    new_client_data = json.loads(request.POST.get('new_client_data'))

    #this needs to be fixed using sessions or something
    rep_company = request.user.mps_user.company
    #**************************************************

    new_client_data['rep_company'] = rep_company

    c = Client(**new_client_data)
    c.save()

    context = {
        'client_id': json.dumps(c.id, cls=DjangoJSONEncoder)
    }
    return HttpResponse(json.dumps(context), content_type="application/json")

#TODO: THIS NEEDS TO BE FIXED
#TODO: 'update'
@login_required
@require_http_methods(['POST'])
def update_proposal_details_page(request):
    proposal_data = json.loads(request.POST.get('proposal_data'))
    proposal_id = request.POST.get('proposal_id')
    # try:
    if proposal_data.get('contract_service_level'):
        proposal_data['contract_service_level'] = ServiceLevel.objects.get(name=proposal_data['contract_service_level'])

    proposal_data['is_deleted'] = False
    Proposal.objects.filter(id=proposal_id).update(**proposal_data)
    # except:
    #     print('there was an issue saving from', update_proposal_details_page)
    #     pass

    context = {
        'proposal_id': proposal_id
    }
    return HttpResponse(json.dumps(context), content_type="application/json")

@login_required
@require_http_methods(['POST'])
def update_client(request, client_id):
    try:
        client = json.loads(request.POST.get('client'))
        Client.objects.filter(id=client_id).update(**client)

        return JsonResponse({'status':'Success', 'msg': 'save successfully'})
    except Client.DoesNotExist:
        return JsonResponse({'status':'Fail', 'msg': 'Object does not exist'})


#TODO: THIS NEEDS TO BE FIXED, this is going to be a little tougher to do since we aren't inheriting from the users class, we have it as a field instead
#TODO: 'update'
@login_required
@require_http_methods(['POST'])
def update_rep(request):
    try:
        obj = request.user.mps_user
        obj.first_name = request.POST['userFirstName']
        obj.last_name= request.POST['userLastName']
        obj.email= request.POST.get('userEmail',False)
        obj.phone_number= request.POST['userNumber']

        obj.save()
        return JsonResponse({'status':'Success', 'msg': 'save successfully'})
    except MPS_User.DoesNotExist:
            return JsonResponse({'status':'Fail', 'msg': 'Object does not exist'})


# @login_required
@require_http_methods(['POST'])
def update_proposal_service_item(request):
    data = json.loads(request.POST.get('proposalServiceItem_data'))

    p_id = data['id']
    p = ProposalServiceItem.objects.get(id=p_id)

    p.total_mono_pages = data['total_mono_pages']
    p.total_color_pages = data['total_color_pages']

    p.transfer_id = data['transfer_id']
    p.transfer_pages = data['transfer_mono_pages'] + data['transfer_color_pages']
    p.transfer_mono_pages = data['transfer_mono_pages']
    p.transfer_color_pages = data['transfer_color_pages']
    
    if p.transfer_pages == 0:
        p.transfer_id = None
    else:
        p.transfer_id = data['transfer_id']

    p.save()

    context = {
        'item_id': json.dumps(p.id, cls=DjangoJSONEncoder)
    }
    return HttpResponse(json.dumps(context), content_type="application/json")

@login_required
@require_http_methods(['POST'])
def update_proposalTCO(request):
    data = json.loads(request.POST.get('proposalTCO_data'))
    proposal_id = data['proposal_id']

    p = ProposalTCO.objects.get(proposal_id=proposal_id)
    p.contract_service_type = data['contract_service_type']
    p.total_supply_spend = data['total_supply_spend']
    p.total_service_spend = data['total_service_spend']
    p.total_lease_spend = data['total_lease_spend']
    p.est_transaction_overhead = data['est_transaction_overhead']
    p.total_sales_orders = data['total_sales_orders']
    p.total_service_orders = data['total_service_orders']

    p.save()

    context = {
        'proposal_id': json.dumps(p.proposal_id, cls=DjangoJSONEncoder)
    }
    return HttpResponse(json.dumps(context), content_type="application/json")

#TODO: THIS NEEDS TO BE FIXED
#TODO: 'update'
@login_required
@require_http_methods(['POST'])
def update_proposal_client_page(request):
    data = json.loads(request.POST.get('data'))
    proposal_id = data['proposal_id']
    client_id = data['client_id']

    p = Proposal.objects.get(id=proposal_id)
    p.client = None if client_id == -1 else Client.objects.get(id=client_id)
    p.is_deleted = False
    p.save()

    context = {
        'proposal_id': json.dumps(p.id, cls=DjangoJSONEncoder)
    }
    return HttpResponse(json.dumps(context), content_type="application/json")



#TODO: THIS NEEDS TO BE FIXED
#TODO: 'create'
@login_required
@require_http_methods(['POST'])
def create_proposal(request):
    now = datetime.now()
    expiration = now + timedelta(days=30)
    proposal = Proposal(status='in-progress',
                    sales_rep=request.user.mps_user, #TODO: Fix current rep
                    management_assumptions=ManagementAssumption.objects.get(company=request.user.mps_user.company),
                    create_date=now,
                    expiration_date=expiration,
                    is_deleted=False)
    proposal.save()

    create_tier_values(proposal)

    context = {
        'proposal_id': json.dumps(proposal.id, cls=DjangoJSONEncoder)
    }
    return HttpResponse(json.dumps(context), content_type="application/json")

# self service update user information
@csrf_exempt
@require_http_methods(['POST'])
def update_proposal_user_info_self_service(request):
    post_dict = request.POST.dict()
    proposal_info = json.loads(post_dict.get('proposal_user'))
    proposal = Proposal.objects.get(pk=proposal_info['proposal'])
    online_client = proposal.client_id

    client = Client.objects.get(pk=online_client)
    print(proposal_info['userdata']['address'])
    client.organization_name = proposal_info['userdata']['organization_name']
    client.email = proposal_info['userdata']['email']
    client.phone_number = proposal_info['userdata']['phone']
    client.city = proposal_info['userdata']['address']['city']
    client.state = proposal_info['userdata']['address']['state']
    client.address = proposal_info['userdata']['address']['street']
    client.zipcode = proposal_info['userdata']['address']['zipcode']
    client.save()

    status = {
        'status': 200,
        'message': 'updated client information'
    }

    return HttpResponse(json.dumps(status), content_type="application/json")

# self service create new proposal
@csrf_exempt
@require_http_methods(['POST'])
def create_proposal_external_source(request):
    post_dict = request.POST.dict()

    post_client = json.loads(post_dict.get('client'))
    company_key = post_dict.get('company_key')
    
    
    company = Company.objects.get(self_service_key=company_key)
    post_client['rep_company'] = str(company.id)

    anon_rep = MPS_User_Anon.objects.get(company=company)
    # get anon rep user
    user = User.objects.get(pk=anon_rep.user.user_id)
    # get mps_user instance
    mps_user = MPS_User.objects.get(user=user)
    post_client['contact'] = mps_user
    
    form = ClientForm(post_client)
    
    if form.is_valid():
        from ramda import empty
        if not empty(post_dict.get('recurring_client')):
            client = form.cleaned_data['recurring_client']
        else: 
            # create the new client
            client = form.save()
            
                
    contract_service_level = ServiceLevel.objects.get(pk=3)
    now = datetime.now()
    expiration = now + timedelta(days=30)
    proposal = Proposal(status='in-progress',
                    sales_rep=mps_user, #TODO: Fix current rep
                    client_id=client.id,
                    management_assumptions=ManagementAssumption.objects.get(company=company),
                    proposal_type='ppc',
                    contract_service_type='total',
                    create_date=now,
                    expiration_date=expiration,
                    contract_service_level=contract_service_level,
                    is_deleted=False)

    proposal.save()

    create_tier_values(proposal)

    context = {
        'proposal_id': json.dumps(proposal.id, cls=DjangoJSONEncoder)
    }

    return HttpResponse(json.dumps(context), content_type="application/json")

def create_tier_values(proposal):
    tiered_values = TieredValue(proposal=proposal)

    tiered_values.save()
    return tiered_values

# self service pull company data based on key
@csrf_exempt
@require_http_methods(['POST'])
def get_company_info_external_source(request):
    post_dict = post_dict = request.POST.dict()
    company_key = post_dict.get('company_key')
    company = Company.objects.get(self_service_key=company_key)
    from django.core import serializers
    context = {
        'company': serializers.serialize('json',[company], cls=DjangoJSONEncoder)
    }

    return HttpResponse(json.dumps(context), content_type="application/json")

# Copied from create_proposal  #punchout  (gel 04/24/2020)
@login_required
@require_http_methods(['POST'])
def punchout_create_proposal(request):
    now = datetime.now()
    expiration = now + timedelta(days=30)
    proposal = Proposal(status='in-progress',
                    sales_rep=request.user.mps_user, #TODO: Fix current rep
                    management_assumptions=ManagementAssumption.objects.get(company=request.user.mps_user.company),
                    create_date=now,
                    expiration_date=expiration,
                    is_deleted=False)
    proposal.save()

#   Not needed?
#   create_tier_values(proposal)

    context = {
        'proposal_id': json.dumps(proposal.id, cls=DjangoJSONEncoder)
    }
    return HttpResponse(json.dumps(context), content_type="application/json")

#def create_tier_values(proposal):
#    tiered_values = TieredValue(proposal=proposal)
#
#    tiered_values.save()
#    return tiered_values


@login_required
@require_http_methods(['POST'])
def punchout_create_client(request):
    new_client_data = json.loads(request.POST.get('new_client_data'))

    #this needs to be fixed using sessions or something
    rep_company = request.user.mps_user.company
    #**************************************************

    new_client_data['rep_company'] = rep_company

    c = Client(**new_client_data)
    c.save()

    context = {
        'client_id': json.dumps(c.id, cls=DjangoJSONEncoder)
    }
    return HttpResponse(json.dumps(context), content_type="application/json")


@login_required
@require_http_methods(['POST'])
def update_assumption(request):
    try:
        assumption_data = json.loads(request.POST.get('assumption_data'))
        mgmt_assmpt = ManagementAssumption.objects.get(company=request.user.mps_user.company)

        for key, value in assumption_data.items():
            # added temp fix to convert int (display value) to dec (stored value)
            if key == 'non_network_margin':
                value = float(value) / 100
            if key == 'percentage_color':
                value = float(value) / 100    
            if isinstance(value, float):
                value = str(value)
            setattr(mgmt_assmpt, key, value)

        mgmt_assmpt.full_clean()
        mgmt_assmpt.save()
        return JsonResponse({'status':'Success'})
    except ValidationError:
        return JsonResponse({'status':'Error', 'msg': 'There was a problem saving your managment assumptions'})

#TODO this will likely be incomplete, but we just need it for right now
#TODO: make this applicable to what harry is doing
#To add a new user from the command line:
#   python manage.py shell
#>>> from mps.views import *
#>>> createNewUser(<username>, <company_id>)
# @login_required
# def create_user(username, company_id):
#     user = User.objects.create_user(username, 'rosehulman')
#     user.save()

#     company = Company.objects.get(id=company_id)
#     mps_user = MPS_User(company=company, user=user)
#     mps_user.save()

@login_required
@require_http_methods(['POST'])
def delete_rep(request):
    try:
        obj = request.user.mps_user
        obj.delete()
        return JsonResponse({'status':'Success', 'msg': 'save successfully'})
    except MPS_User.DoesNotExist:
        return JsonResponse({'status':'Fail', 'msg': 'Object does not exist'})

@login_required
@require_http_methods(['POST'])
def delete_proposal(request):
    proposal_id = request.POST.get('id', None)
    try:
        proposal = Proposal.objects.get(id=proposal_id)
        proposal.is_deleted = True
        proposal.save()
    except:
        return HttpResponse(status=500)
        #should never return false, if it does we have some issues
    return HttpResponse(status=200)

@login_required
@require_http_methods(['GET'])
def get_leasing_data(request):
    leasing_companies = LeasingCompany.objects.filter(company=request.user.mps_user.company)

    leasing_data = []
    for leasing_company in leasing_companies:
        leasing_info = LeasingInfo.objects.filter(leasing_company=leasing_company).order_by('pk')

        data = {
            'leasing_company': leasing_company.leasing_company,
            'company_id': leasing_company.company_id,
            'leasing_info': serializers.serialize('json', leasing_info),
        }
        leasing_data.append(data)

    return JsonResponse(leasing_data, safe=False)

@login_required
@require_http_methods(['POST'])
def calculate_lease_payment(request):
    lease_data = json.loads(request.POST.get('lease_data'))
    leasing_company_name = lease_data['leasing_company']
    lease_type = lease_data['lease_type']
    lease_term = lease_data['lease_term']
    lease_select_type = lease_data['lease_select_type']
    company_id = lease_data['company_id']
    if lease_select_type == 1:
        bundled_amt = 0
    else :
        bundled_amt = Decimal(lease_data['bundled_amt'])
    lease_buyout = Decimal(lease_data['lease_buyout'])
    lease_purchase_price = Decimal(lease_data['lease_purchase_price'])

    lease_term = Decimal(lease_term)
    # Change lease_buyout to be incorporated directly into the equipment price (GEL 05-29-2020)
    #lease_amount = lease_purchase_price + lease_buyout + (bundled_amt * lease_term)
    lease_amount = lease_purchase_price + (bundled_amt * lease_term)

    leasing_company = LeasingCompany.objects.get(leasing_company=leasing_company_name, company_id=company_id)
    leasing_info = LeasingInfo.objects.filter(leasing_company=leasing_company, lease_type=lease_type, lease_term=lease_term)

    lease_rate = 0
    for info in leasing_info:
        if lease_amount <= info.lease_end_range:
            lease_rate = info.lease_rate
            break

    lease_payment = lease_amount * lease_rate
    lease_payment = round(lease_payment, 2)

    return JsonResponse({'lease_payment': lease_payment})

@login_required
@require_http_methods(['POST'])
def save_margin_alert(request, proposal_id):
    margin_alert_data = json.loads(request.POST.get('margin_alert_data'))
    alert_type = margin_alert_data['alert_type']

    margin_alert = ManagerAlert(alert_type=alert_type, proposal_id=proposal_id, company=request.user.mps_user.company, create_date=datetime.now())
    margin_alert.save()

    return JsonResponse({'success': 'success'})
