from django.http import JsonResponse, HttpResponse
from mps.views import setup_part_details_for_costs, year_difference
from django.views.decorators.http import require_http_methods
from mps.self_service import calculateCostPerCartridgeMono, calculateCostPerCartridgeColor
from django.views.decorators.csrf import csrf_exempt
from mps.models import Toner, Proposal, Printer
from decimal import Decimal
from datetime import datetime
from mps.models import *

# calculate CPP
def getRecommendMonoSalesPrice(monoTonerPrice, servicePrice, monoPages, colorPages):
    # format .4
    rcmd_mono_sales_price = float((monoTonerPrice + (servicePrice * monoPages / (monoPages + colorPages))) / monoPages);
    return rcmd_mono_sales_price

def getRecommendColorSalesPrice(colorTonerPrice, servicePrice, monoPages, colorPages):
    # format .4
    rcmd_color_sales_price = float((colorTonerPrice + (servicePrice * colorPages / (monoPages + colorPages))) / colorPages);
    return rcmd_color_sales_price

def getRecommendColorTonerPrice(colorTonerMarginPrice, totalMonthlyColorPages, colorCoverage):
    # format .4
    rcmd_color_toner_price = float(colorTonerMarginPrice * totalMonthlyColorPages * colorCoverage / 0.05);
    return rcmd_color_toner_price

def getRecommendMonoTonerPrice(scaledTonerCPP, pages, monoCoverage):
    #  format .4 
    rcmd_mono_toner_price = float(pages * (scaledTonerCPP * (monoCoverage / 0.05)));
    return rcmd_mono_toner_price

def getRecommendServicePrice(serviceBumpedMarginPrice, totalMonthlyPages):  
    # format .4
    rcmd_service_price = float(serviceBumpedMarginPrice * totalMonthlyPages);
    return rcmd_service_price
    
def getEquipmentPurchasePrice(): 
    return;

# calculate PPC
def getCostPerCartridge(request, proposal_id, printer_id):

    proposal = Proposal.objects.get(pk=proposal_id)
    printer = Printer.objects.get(pk=printer_id)

    ppc_mono = calculateCostPerCartridgeMono(proposal, printer)
    ppc_color = calculateCostPerCartridgeColor(proposal, printer)

    return JsonResponse({
        'ppc_mono': ppc_mono,
        'ppc_color': ppc_color
    })

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

    return JsonResponse(Decimal(service_rate))

@csrf_exempt
@require_http_methods(['POST'])
def create_proposal_network_device_self_service(request, proposal_id):
    import json
    service_info = json.loads(request.POST.get('proposed_service'))
    service_info['proposal'] = Proposal.objects.get(id=proposal_id)
    
    purchased_items = service_info['proposed_service']['purchased_items']
    variants = service_info['proposed_service']['variants']
    
    new_service_items = generate_service_items(purchased_items, variants, proposal_id)
    return JsonResponse({'new_service_items': new_service_items})

def generate_service_items(items, variants, proposal_id):
    import json
    
    proposal_service_info = dict()
    proposed_purchase_info = list()

    for item in items:
        details = item['details']
        printer = Printer.objects.get(pk=details['device'])
        proposal = Proposal.objects.get(pk=proposal_id)

        mps_user = MPS_User.objects.get(pk=proposal.sales_rep_id)
        user = User.objects.get(pk=mps_user.user_id)
        assumption = ManagementAssumption.objects.get(company=mps_user.company)

        proposal_service_info.update({'printer': printer})
        proposal_service_info.update({'proposal': proposal})
        proposal_service_info.update({ 'is_non_network': True })
        
        is_non_network = True
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

        proposal_service_info.update({'tier_level_mono': tier_level_mono})
        proposal_service_info.update({'tier_level_color': tier_level_color})
        
        

        proposal_service_info.update({'base_volume_mono': details['page_cost_details']['def_base_volume_mono']}) 
        proposal_service_info.update({'base_rate_mono': details['page_cost_details']['def_base_rate_mono']})
        proposal_service_info.update({'base_volume_color': details['page_cost_details']['def_base_volume_color']})
        proposal_service_info.update({'base_rate_color': details['page_cost_details']['def_base_rate_color']})
        
        proposal_service_info.update({'mono_coverage': '0.05'})
        proposal_service_info.update({'color_coverage': '0.05'})
        
        proposal_service_info.update({'proposed_cpp_mono': "{:.2f}".format(details['rcmdPricing']['sf_mono_price'])})
        proposal_service_info.update({'proposed_cpp_color': "{:.2f}".format(details['rcmdPricing']['sf_color_price'])})
        
        proposal_service_info.update({'mono_toner_price': "{:.2f}".format(details['rcmdPricing']['rcmdMonoToner'])})
        proposal_service_info.update({'color_toner_price': "{:.2f}".format(details['rcmdPricing']['rcmdColorToner'])})

        proposal_service_info.update({'service_cost': "{:.2f}".format(details['rcmdPricing']['rcmdService'])})
        
        proposal_service_info.update({'total_mono_pages': details['printer_details']['avm_mono']})
        proposal_service_info.update({'total_color_pages': details['printer_details']['avm_color']})
        
        proposal_service_info.update({'estimated_commission': '0'})
        proposal_service_info.update({'number_printers_serviced': 1})
        # mono_toner_price = models.DecimalField(decimal_places=5, max_digits=12, null=True, blank=True)
        # color_toner_price = models.DecimalField(decimal_places=5, max_digits=12, null=True, blank=True)

        new_printer_item = ProposalServiceItem(**proposal_service_info)
        
        if not is_non_network:
            new_printer_item.set_recommended_mono_cost_per_cartridge()
            new_printer_item.set_recommended_color_cost_per_cartridge()
        
        
        new_printer_item.full_clean()
        new_printer_item.save()
        

        printer_costs = details['printer_costs']
        new_purchase_info = generate_purchase_info(printer_costs, variants, proposal, new_printer_item, mps_user.company, printer, tier_level_mono, tier_level_color)

        proposed_purchase_info.extend(new_purchase_info)
    
    return proposed_purchase_info

def generate_purchase_info(printer_costs, variants, proposal, new_printer_item, company, printer, tier_level_mono, tier_level_color):
    from django.shortcuts import get_object_or_404
    new_purchase_item_reciept = list()

    if len(printer_costs) > 0:
        for item in printer_costs:
            # print(printer_costs[item])
            if(item in variants):
                purchase_info = dict()
                printer_cost_item = get_object_or_404(PrinterCost, long_model=printer_costs[item]['model_name'], company=company)
                purchase_info.update({'buy_or_lease': 'buy'})
                purchase_info.update({'proposed_cost': printer_cost_item.price.replace('$','').replace(',','')})
                purchase_info.update({'duty_cycle': printer.duty_cycle})
                purchase_info.update({'long_model': printer_costs[item]['model_name']})
                purchase_info.update({'out_cost': "{:.4f}".format(printer_costs[item]['outCost'])})
                purchase_info.update({'msrp_cost': "{:.4f}".format(printer_costs[item]['msrp'])})
                purchase_info.update({'care_pack_cost': "{:.4f}".format(printer_costs[item]['carePackCost'])})
                purchase_info.update({'estimated_commission': '0'})
                purchase_info.update({'number_printers_purchased': 1})

                new_purchase_item_id = ''
                if purchase_info:
                    purchase_info.update({'printer': printer})
                    purchase_info.update({'proposal': proposal})

                    new_purchase_item = ProposalPurchaseItem(**purchase_info)
                    # new_purchase_item.set_recommended_mono_cost_per_cartridge()
                    # new_purchase_item.set_recommended_color_cost_per_cartridge()
                    new_purchase_item.full_clean()
                    new_purchase_item.save()
                    new_printer_item.proposal_purchase_item = new_purchase_item
                    new_purchase_item_id = new_purchase_item.id
                    new_printer_item.save()

                new_purchase_item_reciept.append({
                        'service_item_id': new_printer_item.id,
                        'purchase_item_id': new_purchase_item_id,
                        'mono_tier': tier_level_mono,
                        'color_tier': tier_level_color
                    })
            else:
                # variants are not selected what do we assume here that they want all variants? currently just add the printer.
                purchase_info = dict()
                purchase_info.update({'buy_or_lease': 'buy'})
                purchase_info.update({'duty_cycle': printer.duty_cycle})
                purchase_info.update({'estimated_commission': '0'})
                purchase_info.update({'proposed_cost': '0'})
                purchase_info.update({'long_model': "{} {}".format(printer.make, printer.short_model)})
                purchase_info.update({'out_cost': '0'})
                purchase_info.update({'msrp_cost': '0'})
                purchase_info.update({'care_pack_cost': '0'})
                purchase_info.update({'estimated_commission': '0'})
                purchase_info.update({'number_printers_purchased': 1})
                new_purchase_item_id = ''
                if purchase_info:
                    purchase_info.update({'printer': printer})
                    purchase_info.update({'proposal': proposal})

                    new_purchase_item = ProposalPurchaseItem(**purchase_info)
                    # new_purchase_item.set_recommended_mono_cost_per_cartridge()
                    # new_purchase_item.set_recommended_color_cost_per_cartridge()
                    new_purchase_item.full_clean()
                    new_purchase_item.save()
                    new_printer_item.proposal_purchase_item = new_purchase_item
                    new_purchase_item_id = new_purchase_item.id
                    new_printer_item.save()

                new_purchase_item_reciept.append({
                        'service_item_id': new_printer_item.id,
                        'purchase_item_id': new_purchase_item_id,
                        'mono_tier': tier_level_mono,
                        'color_tier': tier_level_color
                    })
                break;
        new_purchase_item.number_printers_purchased = len(new_purchase_item_reciept)
        new_purchase_item.save()
    else:
        # whatever specs the printer itself has no variants
        purchase_info = dict()
        purchase_info.update({'buy_or_lease': 'buy'})
        purchase_info.update({'duty_cycle': printer.duty_cycle})
        purchase_info.update({'estimated_commission': '0'})
        purchase_info.update({'proposed_cost': '0'})
        purchase_info.update({'long_model': "{} {}".format(printer.make, printer.short_model)})
        purchase_info.update({'out_cost': '0'})
        purchase_info.update({'msrp_cost': '0'})
        purchase_info.update({'care_pack_cost': '0'})
        purchase_info.update({'estimated_commission': '0'})
        purchase_info.update({'number_printers_purchased': 1})
        new_purchase_item_id = ''
        if purchase_info:
            purchase_info.update({'printer': printer})
            purchase_info.update({'proposal': proposal})

            new_purchase_item = ProposalPurchaseItem(**purchase_info)
            # new_purchase_item.set_recommended_mono_cost_per_cartridge()
            # new_purchase_item.set_recommended_color_cost_per_cartridge()
            new_purchase_item.full_clean()
            new_purchase_item.save()
            new_printer_item.proposal_purchase_item = new_purchase_item
            new_purchase_item_id = new_purchase_item.id
            new_printer_item.save()

        new_purchase_item_reciept.append({
                'service_item_id': new_printer_item.id,
                'purchase_item_id': new_purchase_item_id,
                'mono_tier': tier_level_mono,
                'color_tier': tier_level_color
            })
        
    return new_purchase_item_reciept