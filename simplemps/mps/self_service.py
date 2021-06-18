from django.shortcuts import render
from django.shortcuts import redirect
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from .controllers.model_update import create_tier_values
from .models import Company, Proposal, AccountSetting, ManagementAssumption, MPS_User, Make, ModelSpecification, Printer, PrinterCost, ProposalServiceItem, ProposalPurchaseItem, Client, ServiceLevel, TieredValue, PageCost, Accessory, Toner, MPS_User_Anon
from .views import calculate_mono_cpp, calculate_color_cpp, get_proposal_tco_items, prep_proposal_service_items_list, get_network_device_details, calculate_service_rate, setup_part_details_for_costs, year_difference
from . forms import AccountSettingForm, SignatureForm, ClientForm
from jsignature.utils import draw_signature
from django.conf import settings
from django.http import JsonResponse
from decimal import Decimal
from .controllers.utils import convert_class_to_primitives, get_flat_rate

OEM = 'OEM'
OEM_SMP = 'OEM_SMP'
REMAN = 'REMAN'
MANUFACTURER_CHOICES = (
    (OEM, 'OEM'),
    (REMAN, 'Reman'),
    (OEM_SMP, 'OEM SMP')
)


def get_self_service_landing(request, client_self_service_key):
    company = Company.objects.get(self_service_key=client_self_service_key)
    settings = AccountSetting.objects.get(company=company)

    # check if this company doesn't sell hardware.
    mgmt_assumpts = ManagementAssumption.objects.get(company=company)
    sells_hardware = mgmt_assumpts.sells_hardware

    # print(request.user.groups.filter(name__in=["Admin", "Manager", "Representative"]).exists())

    if request.method == 'GET':

        form = ClientForm()
        form.fields['rep_company'].initial = company

        context = {
            'co_branding_logo': settings.co_branding_logo.url,
            'is_landing': True,
            'client_self_service_key': company.self_service_key,
            'clientForm': form,
            'sells_hardware': sells_hardware,
            'is_staff': request.user.groups.filter(name__in=["Admin","Manager","Representative"]).exists()
        }  

        return render(request, 'self_service/detail.html', context)
       
    elif request.method == 'POST':
        
        if(request.user.is_anonymous):
            # pull anon representative
            try: 
                anon_rep = MPS_User_Anon.objects.get(company=company)
            except MPS_User_Anon.DoesNotExist:
                form = ClientForm()
                form.fields['rep_company'].initial = company
                
                from django.contrib import messages
                messages.error(request, 'MPS User Anon doesn\'t exist.')

                context = {
                    'co_branding_logo': settings.co_branding_logo.url,
                    'is_landing': True,
                    'client_self_service_key': company.self_service_key,
                    'clientForm': form,
                    'is_staff': request.user.groups.filter(name__in=["Admin","Manager","Representative"]).exists(),
                    
                }

                return render(request, 'self_service/detail.html', context)

            # get mps user instance
            user = User.objects.get(pk=anon_rep.user.user_id) 
            
        else: 
            user = request.user
            
        mps_user = MPS_User.objects.get(user=user)
        
        post_dict = request.POST.dict()
        form = ClientForm(request.POST)
        
        if form.is_valid(): 
            from ramda import empty
            if not empty(post_dict.get('recurring_client')):
                client = form.cleaned_data['recurring_client']
            else: 
                # create the new client
                client = form.save()
                
        else: 
            context = {
                'co_branding_logo': settings.co_branding_logo.url,
                'is_landing': True,
                'client_self_service_key': company.self_service_key,
                'clientForm': form,
                'is_staff': request.user.groups.filter(name__in=["Admin","Manager","Representative"]).exists()
            }
            return render(request, 'self_service/detail.html', context)
        
        contract_service_level = ServiceLevel.objects.get(pk=3)

        proposal = Proposal(
                    status='in-progress', management_assumptions=ManagementAssumption.objects.get(company=company),
                    create_date=datetime.now(), expiration_date=datetime.now() + timedelta(days=30), is_deleted=True,
                    contract_service_type='total', proposal_type='ppc',sales_rep=mps_user, client_id=client.id, contract_service_level=contract_service_level)
        
        
        # if request.POST['is_supplies_only'] == True:
        #     proposal.contract_service_type = 'supplies_only'
        # else: 
        #     proposal.contract_service_type = 'total'

        # if request.POST['is_pricing_per_page'] == True: 
        #     proposal.proposal_type = 'cpp'
        # else: 
        #     proposal.proposal_type = 'ppc'

        
        if form.cleaned_data['is_supplies_only'] == 'True':
            proposal.contract_service_type = 'supplies_only'

        if form.cleaned_data['is_pricing_per_page'] == 'True': 
            proposal.proposal_type = 'cpp'

        proposal.save()

        create_tier_values(proposal)
        
        if(sells_hardware != True): 
            return redirect('/self-service/{self_service_key}/{proposal_id}/selection'.format(
            self_service_key=client_self_service_key, proposal_id=proposal.id))

        return redirect('/self-service/{self_service_key}/{proposal_id}/equipment'.format(
            self_service_key=client_self_service_key, proposal_id=proposal.id))


def get_self_service_equipment(request, client_self_service_key, proposal_id):
    company = Company.objects.get(self_service_key=client_self_service_key)
    proposal = Proposal.objects.get(id=proposal_id)
    settings = AccountSetting.objects.get(company=company)
    owned_product_id = []

    brand_options = {obj['id']: obj['name'] for obj in Make.objects.values('name', 'id').distinct()}
    print_technology_options = [obj['print_technology'] for obj in
                                ModelSpecification.objects.values('print_technology').distinct()]
    max_papersize_options = [obj['papersize_max'] for obj in
                             ModelSpecification.objects.values('papersize_max').distinct()]
    o_adf_capacity_options = [str(obj['o_adf_capacity']) for obj in
                              ModelSpecification.objects.values('o_adf_capacity').distinct()]
    mono_print_speed_options = [str(obj['ppm_mono']) for obj in
                                ModelSpecification.objects.values('ppm_mono').distinct()]
    color_print_speed_options = [str(obj['ppm_color']) for obj in
                                 ModelSpecification.objects.values('ppm_color').distinct()]
    context = {
        'co_branding_logo': settings.co_branding_logo.url,
        'is_equipment': True,
        'client_self_service_key': company.self_service_key,
        'proposal_id': proposal.id,
        'company_name': company.name,
        'company_owner': company.owner,
        'company_email': company.email,
        'company_phone_number': company.phone_number,
        'company_city': company.city,
        'company_state': company.state,
        'company_zip_code': company.zipcode,
        'company_country': company.country,
        'show_instructions': True,
        'brand': brand_options,
        'print_technology': print_technology_options,
        'max_papersize': max_papersize_options,
        'o_adf_capacity': o_adf_capacity_options,
        'color_print_speed': color_print_speed_options,
        'mono_print_speed': mono_print_speed_options,
    }

    if request.method == 'GET':
        return render(request, 'self_service/equipment.html', context)
    elif request.method == 'POST':
        # clear the filter list
        if(request.POST['filter'] == 'clear'): 
            context.update({'show_instructions': True})
            return render(request, 'self_service/equipment.html', context) 

        if(request.POST['equipment_type_new'] == 'True'): 
            # list new products only
            cost_table = PrinterCost.objects.filter(company=company)
            results = ModelSpecification.objects.filter(mfg_model_number__in=[i.product_id for i in cost_table], available=True)
        else:
            return redirect('/self-service/{self_service_key}/{proposal_id}/selection'.format(self_service_key=client_self_service_key, proposal_id=proposal.id))
            
            # including owned products
            cost_table = PrinterCost.objects.all()
            owned_printers = PrinterCost.objects.filter(company_id=company.id).values()
            owned_product_id = [i['product_id'] for i in owned_printers]
            results = ModelSpecification.objects.filter(printer_id__in=[i.printer_id for i in cost_table], available=True)
            
        context.update({'show_instructions': False})
        brand_items = [request.POST[item] for item in request.POST if 'brand' in item]
        print_technology_items = [request.POST[item] for item in request.POST if 'print_technology' in item]
        max_papersize_items = [request.POST[item] for item in request.POST if 'max_papersize' in item]
        adf_capacity_items = [request.POST[item] for item in request.POST if 'adf_capacity' in item]
        mono_print_speed_items = [request.POST[item] for item in request.POST if 'mono_print_speed' in item]
        color_print_speed_items = [request.POST[item] for item in request.POST if 'color_print_speed' in item]
        
        if len(brand_items):
            kw = {"printer__make__id__in": brand_items}
            results = results.filter(**kw)
        if len(print_technology_items):
            kw = {"print_technology__in": print_technology_items}
            results = results.filter(**kw)
        if len(max_papersize_items):
            kw = {"papersize_max__in": max_papersize_items}
            results = results.filter(**kw)
        if len(adf_capacity_items):
            kw = {"o_adf_capacity__in": adf_capacity_items}
            results = results.filter(**kw)
        if len(mono_print_speed_items):
            kw = {"ppm_mono__in": mono_print_speed_items}
            results = results.filter(**kw)
        if len(color_print_speed_items):
            kw = {"ppm_color__in": color_print_speed_items}
            results = results.filter(**kw)
        # if len(price): 
        #     kw = {"price": price}
        #     results= results.filter(**kw)

        if request.POST.get('is_color') and request.POST.get('is_mono'):
            pass
        elif request.POST.get('is_color'):
            results = results.filter(printer__is_color_device=True)
        elif request.POST.get('is_mono'):
            results = results.filter(printer__is_color_device=False)

        fields = {field: True for field in request.POST if
              field.startswith('f_') or field.startswith('c_') or field.startswith('o_')}

        result_set = [q for q in results]
        for field, field_value in fields.items():
            result_set += results.filter(**{field: field_value})

        results = list(set(results))
        
        # check if any models are owned
        def isModelOwned(result):
            
            printer = Printer.objects.get(pk=result.printer_id)
            result_json = result.as_json()
            mfg_model_number = result_json.get('mfg_model_number')

            result_json['isOwned'] = True if mfg_model_number in owned_product_id else False
            price, cost_id = result.get_item_price(company)

            result_json['price'] = price
            result_json['cost_id'] = cost_id

            # get network device details so there are less api calls.
            result_json['device_net_details'] = get_network_device_details(request, printer.id, proposal_id, company)

            # we want to see ppc without needing to create a proposed service item
            if proposal.proposal_type == 'ppc': 
                result_json['recommended_mono_ppc'] = calculateCostPerCartridgeMono(proposal, printer);
                result_json['recommended_color_ppc'] = calculateCostPerCartridgeColor(proposal, printer);

            return result_json

        search_results = {
            'printers':[isModelOwned(obj) for obj in results],
            'proposal_details': { 'proposal': { 'id': proposal_id } },
            'company': company.id,
            'is_cpp': proposal.proposal_type,
            'num_results': len(results),
            'company_name': company.name
            }
        
        import json
        from django.core.serializers.json import DjangoJSONEncoder

        context.update({
            'results':json.dumps(search_results, cls=DjangoJSONEncoder),
            })

        return render(request, 'self_service/equipment.html', context)

def get_self_service_selection(request, client_self_service_key, proposal_id):
    proposal = Proposal.objects.get(id=proposal_id)
    company = Company.objects.get(self_service_key=client_self_service_key)
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
    import json
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
        'client': proposal.client.organization_name,
        'client_self_service_key': company.self_service_key,
        'path': 'rep/newProposal/pricing.html',
        'is_self_service_review_selection': True,
    }
    return render(request,'self_service/selection-review.html', context)
    # return render(request,'self_service/selection-review-self-service.html', context)

def get_self_service_review(request, client_self_service_key, proposal_id):   
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
    company = Company.objects.get(self_service_key=client_self_service_key)
    sales_rep_user = User.objects.get(pk=sales_rep.user.id)
    service_level = ServiceLevel.objects.get(pk=proposal.contract_service_level.id)
    account_settings = AccountSetting.objects.filter(company=company).order_by('-pk')[0]
    if proposal.proposal_type == 'cpp':
        proposal.term = 36
    else:
        proposal.term = 12

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
        ppc_mono = 0
        ppc_color = 0
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
            ppc_mono = item.proposed_cost_per_cartridge_mono if (item.proposed_cost_per_cartridge_mono or 0) > 0 else item.recommended_cost_per_cartridge_mono
            ppc_color = item.proposed_cost_per_cartridge_color if (item.proposed_cost_per_cartridge_color or 0) > 0 else item.recommended_cost_per_cartridge_color
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
            'ppc_mono': ppc_mono,
            'ppc_color': ppc_color,
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

    # import code; code.interact(local=dict(globals(), **locals()))
    if proposal.status == 'in-progress':
        signature_form = SignatureForm()

    elif proposal.status == 'proposal_accepted' and proposal.signature_image.name is not '':
        signature_form = settings.WEB_DOMAIN + proposal.signature_image.url
    else:
        signature_form = None

    proposal_path = "proposal/"+str(company.id)+'_cpp.html' if proposal.proposal_type == 'cpp' else "proposal/"+str(company.id)+"_ppc.html"
    
    context = {
        'service_items': service_items,
        'proposal': {
            'id': proposal_id,
            'logo': account_settings.logo,
            'term': proposal.term,
            'status': proposal.status,
            'response_time': service_level.responseTime,
            'service_type': proposal.contract_service_type,
            'proposal_type': proposal.proposal_type,
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
        'form': signature_form,
        'is_self_service_review_selection': True,
        'is_review_proposal': True,
        'path': proposal_path,
        'client_self_service_key': company.self_service_key,
        'proposal_id': proposal_id
    }
    
    return render(request, 'self_service/proposal-review.html', context)


def get_network_device_details(request, device_id, proposal_id, company):
    
    try:
        proposal = Proposal.objects.get(id=proposal_id)

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
        all_printer_costs = PrinterCost.objects.filter(printer__id=device_id, company=company)
        # printer_costs = {}
        printer_costs = []
        for p_cost in all_printer_costs:
            printer_costs.append( {
                'id': p_cost.id,
                'product_id': p_cost.product_id,
                'model_name': p_cost.long_model,
                'outCost': float(p_cost.out_cost or 0.00),
                'msrp': float(p_cost.msrp_cost or 0.00),
                'carePackCost': float(p_cost.care_pack_cost or 0.00)
            })

        # 2. printer details
        #    add avm values to data pool
        printer = Printer.objects.get(id=device_id)
        printer_details = {
            'printer_is_color_type': printer.is_color_device,
            'release_date': printer.release_date,
            'make': printer.make.name,
            'device_type': printer.device_type,
            'avm_color': printer.avm_color,
            'avm_mono': printer.avm_mono,
            'duty_cycle': printer.duty_cycle
        }
        
        # 3. toner costs
        toners_cost = {}
        # removed -1 and - ((proposal.term / 12) / 100)
        margin_toner_rate = float(mgmt_assumpts.target_margin_toner) 

        black_cost_per_page = calculate_mono_cpp(short_model=printer.short_model, proposal_id=proposal_id, company=company)
        color_cost_per_page = calculate_color_cpp(short_model=printer.short_model, proposal_id=proposal_id, company=company) if printer.is_color_device else None
       
        if black_cost_per_page is None or (printer.is_color_device and color_cost_per_page is None):
            toners_cost['warning'] = 'No avaiable toner or drum or developer for this printer model in databse'
            context = {
                'printer_costs': printer_costs,
                'printer_details': printer_details,
                'toners_costs': toners_cost
            }
            return context
        
        toners_cost['scaled_mono_cost'] = (black_cost_per_page / cost_multiplier) / (1 - Decimal(margin_toner_rate))
        toners_cost['scaled_color_cost'] = (color_cost_per_page / cost_multiplier) / (1 - Decimal(margin_toner_rate)) if printer.is_color_device else 0
        
        # 4. service costs
        page_costs = PageCost.objects.get(printer__id=device_id, company=company)
        
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
    
    return context

# calculate PPC
def calculateCostPerCartridgeMono(proposal, printer):
    if proposal.default_toner_type == 'OEM_SMP':
        toner = Toner.objects.filter(company_id=proposal.sales_rep.company_id, printer_id=printer,
                                        part_color='mono', manufacturer='OEM_SMP').first()
    elif proposal.default_toner_type == 'REMAN':
        toner = Toner.objects.filter(company_id=proposal.sales_rep.company_id, printer_id=printer,
                                        part_color='mono', manufacturer='REMAN').first()
    else:
        toner = Toner.objects.filter(company_id=proposal.sales_rep.company_id, printer_id=printer,
                                        part_color='mono', manufacturer='OEM').first()

    if printer.mono_toner and toner and toner.price:
        recommended_cost_per_cartridge_mono = round(
            (Decimal(toner.price) * Decimal((1 + proposal.management_assumptions.managed_cartridge_inflate))) / (
                Decimal(1 - proposal.management_assumptions.target_margin_toner)), 2)
    else:
        recommended_cost_per_cartridge_mono = Decimal('0.0000')

    return recommended_cost_per_cartridge_mono;


def calculateCostPerCartridgeColor(proposal, printer):
    if proposal.default_toner_type == 'OEM_SMP':
        toner = Toner.objects.filter(company_id=proposal.sales_rep.company_id, printer_id=printer,
                                        part_color='cyan', manufacturer='OEM_SMP').first()
    elif proposal.default_toner_type == 'REMAN':
        toner = Toner.objects.filter(company_id=proposal.sales_rep.company_id, printer_id=printer,
                                        part_color='cyan', manufacturer='REMAN').first()
    else:
        toner = Toner.objects.filter(company_id=proposal.sales_rep.company_id, printer_id=printer,
                                        part_color='cyan', manufacturer='OEM').first()

    if printer.cyan_toner and toner and toner.price:
        recommended_cost_per_cartridge_color = round(
            (Decimal(toner.price) * Decimal(
                (1 + proposal.management_assumptions.managed_cartridge_inflate))) / (
                Decimal(1 - proposal.management_assumptions.target_margin_toner)), 2)
    else:
        recommended_cost_per_cartridge_color = Decimal('0.0000')
    return recommended_cost_per_cartridge_color;

def get_self_service_selection_landing(request, client_self_service_key):
    return render(request, 'self_service/selection-review-self-service.html')