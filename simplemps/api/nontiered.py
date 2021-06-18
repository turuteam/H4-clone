from mps.models import ProposalServiceItem, ProposalPurchaseItem, ManagementAssumption, PrinterCost, MPS_User, Proposal, Company

# function updateModalUI() {
#     const pageInfo = {
#         monoMonthly: parseInt($('#total-monthly-mono-pages').val()) || 0,
#         colorMonthly: parseInt($('#total-monthly-color-pages').val()) || 0,
#         monoCoverage: parseFloat($('#mono-coverage').val()) || 0,
#         colorCoverage: parseFloat($('#color-coverage').val()) || 0
#     }
#     pageInfo.totalMonthly =  pageInfo.monoMonthly + pageInfo.colorMonthly;
#     $('#total-monthly-pages').val(pageInfo.totalMonthly);

#     const recommendedPrice = {
#         monoToner: updateRecommendMonoTonerPrice(toner_costs.scaled_mono_cost, pageInfo.monoMonthly, pageInfo.monoCoverage),
#         colorToner: updateRecommendColorTonerPrice(toner_costs.scaled_color_cost, pageInfo.colorMonthly, pageInfo.colorCoverage),
#         service: updateRecommendServicePrice(toner_costs.scaled_service_cost, pageInfo.totalMonthly),
#     };
#     recommendedPrice.monoSales =  updateRecommendMonoSalesPrice(recommendedPrice.monoToner, recommendedPrice.service, pageInfo.monoMonthly, pageInfo.colorMonthly);
#     recommendedPrice.colorSales = updateRecommendColorSalesPrice(recommendedPrice.colorToner, recommendedPrice.service, pageInfo.monoMonthly, pageInfo.colorMonthly);
#     recommendedPrice.monthly = updateRecommendMonthlyPrice(recommendedPrice.monoToner, recommendedPrice.colorToner, recommendedPrice.service);

#     const proposedPrice = {
#         baseMonoVolume: parseInt($('#base-volume-mono').val()) || 0,
#         baseColorVolume: parseInt($('#base-volume-color').val()) || 0,
#         baseMonoRate: parseFloat($('#base-rate-mono').val()) || 0,
#         baseColorRate: parseFloat($('#base-rate-color').val()) || 0,
#         monoSalesPrice: parseFloat($('#proposed-mono-sales').val()) || 0,
#         colorSalesPrice: parseFloat($('#proposed-color-sales').val()) || 0,
#     };

#     let device_type;
#     const id = $('add-network-device').data('id');

#     if (id) {
#         device_type = p_objects[id].service.device_type
#     } else if (printer_details !== undefined) {
#         device_type = printer_details.device_type;
#     }

#     // if margin locked, see if proposed pricing need to be adjusted  (gel 2019-11-25)
#     // otherwise just save any possible changes in case switch is changed back
#     if($('#lock-margin').val() == '1') {
#         let changeType = "unknown";
#         equalizeMargin(changeType);             
#     } else {
#         $('#saved-mono-sales').val($('#proposed-mono-sales').val());
#         $('#saved-color-sales').val($('#proposed-color-sales').val());
#     }

#     if (device_type) {
#         updateNetDeviceCommission(device_type, pageInfo, recommendedPrice, proposedPrice);
#     }
# }

# function updateMonthlyPages(monoPages, colorPages) {
#     $('#total-monthly-pages').val(monoPages + colorPages);
#     return monoPages + colorPages;
# }

# function updateMonthlyTotals() {
#     let netPriceTotal = runningColorPrice + runningMonoPrice + runningMonoColorPrice;
#     $('#monthlyNetPrice').text('$' + addThousandsSeparator(netPriceTotal.toFixed(2)));
#     $('#monthlyNetPrice').attr('val', addThousandsSeparator(netPriceTotal.toFixed(2)));

#     let netCostTotal = runningColorCost + runningMonoCost + runningMonoColorCost;
#     let netMargin = netPriceTotal == 0 ? 0 : ((netPriceTotal - netCostTotal) / netPriceTotal * 100).toFixed(0);

#     $('#netMargin').text(netMargin + '%');

#     if (netMargin / 100 < (mgmtAsmpts.min_mono_margin + mgmtAsmpts.min_mono_on_color_margin + mgmtAsmpts.min_color_margin) / 3) {
#         $('#netMargin').addClass('warning');
#     } else {
#         $('#netMargin').removeClass('warning');
#     }

#     let nonNetTotal = 0;
#     $.each(p_objects, function (index, device) {
#         device = device.service;
#         if (!device.is_non_network) {
#             return;
#         }

#         nonNetTotal += (device.non_network_cost * device.number_printers_serviced);
#     });
#     $('#monthlyNonNetPrice').text('$' + addThousandsSeparator(nonNetTotal.toFixed(2)));

#     let monthlyLease = 0;
#     let equipmentBought = 0;
#     $.each(proposal_purchase_items, function (index, item) {
#         if (item.buy_or_lease === 'buy') {
#             equipmentBought += parseFloat(item.proposed_cost);
#         } else {
#             monthlyLease += parseFloat(item.lease_payment);
#         }
#     });
#     $('#monthly-lease').text('$' + addThousandsSeparator(monthlyLease.toFixed(2)));
#     $('#monthly-lease').attr('val', addThousandsSeparator(monthlyLease.toFixed(2)));
#     $('#equipment-bought').text('$' + addThousandsSeparator(equipmentBought.toFixed(2)));
    
#     let monthlyCommission = 0;
#     let monthlyMPSCommission = 0;
#     let monthlyEQCommission = 0;
#         $.each(proposal_service_items, function (index, item) {
#             monthlyMPSCommission += parseFloat(item.estimated_commission);
#         });

#         $.each(proposal_purchase_items, function (index, item) {
#             monthlyEQCommission += parseFloat(item.estimated_commission);
#         });

#         monthlyCommission = monthlyMPSCommission + monthlyEQCommission;

#     $('#total-monthly-commission').text('$' + addThousandsSeparator(monthlyCommission.toFixed(2)));
#     $('#monthly-commission').text('$' + addThousandsSeparator(monthlyMPSCommission.toFixed(2)));
#     $('#monthly-eq-commission').text('$' + addThousandsSeparator(monthlyEQCommission.toFixed(2)));

#     let totalPrice = netPriceTotal + nonNetTotal + monthlyLease;
#     $('#monthlyTotalPrice').text('$' + addThousandsSeparator(totalPrice.toFixed(2)));
# }

# function updateNetDeviceCommission(deviceType, pageInfo, recommendedPrice, proposedPrice) {
#     let NetDeviceCommission = 0;
#     let price = recommendedPrice.monthly;
#     let cost = recommendedPrice.monthly * (1-((mgmtAsmpts.target_margin_toner + mgmtAsmpts.target_margin_service)/2));

#     if ( Object.values(proposedPrice).some(each => Boolean(each)) ) {
#         const base = proposedPrice.baseMonoRate + proposedPrice.baseColorRate;
#         const mono = proposedPrice.monoSalesPrice * (pageInfo.monoMonthly - proposedPrice.baseMonoVolume);
#         const color = proposedPrice.colorSalesPrice * (pageInfo.colorMonthly - proposedPrice.baseColorVolume);

#         price = base + mono + color;

#     }

#     switch (mgmtAsmpts.commission_type) {
#         case 'flat_margin':
#             NetDeviceCommission = mgmtAsmpts.percent_margin_flat_rate * (price - cost);
#             $('#commission').html(`${NetDeviceCommission.toFixed(2)}`);
#             break;
#         case 'flat_revenue':
#             NetDeviceCommission = mgmtAsmpts.percentage_revenue_flat_rate * price;
#             $('#commission').html(`${NetDeviceCommission.toFixed(2)}`);
#             break;
#         case 'blended_margin':
#             NetDeviceCommission = (deviceType == 'printer' ? mgmtAsmpts.margin_rate_printers : mgmtAsmpts.margin_rate_copiers) * (price - cost);
#             $('#commission').html(`${NetDeviceCommission.toFixed(2)}`);
#             break;
#         case 'blended_revenue':
#             NetDeviceCommission = (deviceType == 'printer' ? mgmtAsmpts.revenue_rate_printers : mgmtAsmpts.revenue_rate_copiers) * price;
#             $('#commission').html(`${NetDeviceCommission.toFixed(2)}`);
#             break;
#         default:

#     }
# }

# function updateNonNetDeviceComission(unitCommission) {
#     let nonNetworkDeviceQuantity = $('#nonNetworkDevice-quantity').val();
#     $('#nonNetwork-commission').text('$ ' + (unitCommission * nonNetworkDeviceQuantity).toFixed(2));
# }

# function updateNonNetTotalPrice(unitPrice) {
#     $('#nonNetworkDevice-total-price').val(($('#nonNetworkDevice-quantity').val() * unitPrice).toFixed(2));
# }

# function updateOverallMargin() {
#     $('#margin').val(($('#equipment-purchase-price').val() - $('#total-outcost').val()).toFixed(2));
#     $('#margin-percentage').val(($('#margin').val() / $('#equipment-purchase-price').val() * 100).toFixed(2));
#     if($('#leaseBuyout').val()===""){
#         $('#leaseBuyout').val(0);
#     }    
#     if($('#rentBuyout').val()===""){
#         $('#rentBuyout').val(0);
#     }   
#     if($('#equipment-purchase-price').val()===""){
#         $('#equipment-purchase-price').val(0);
#     }
#     $('#leasePurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#leaseBuyout').val());
#     $('#rentPurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#rentBuyout').val());
#     updateEquipmentCommissions();
# }

# function updatePercent() {
#     $('#equipment-purchase-price').val(($('#total-outcost').val() / (1 - ($('#margin-percentage').val()/100))).toFixed(2));
#     if($('#leaseBuyout').val()===""){
#         $('#leaseBuyout').val(0);
#     }
#     if($('#rentBuyout').val()===""){
#         $('#rentBuyout').val(0);
#     }
#     if($('#equipment-purchase-price').val()===""){
#         $('#equipment-purchase-price').val(0);
#     }
#     $('#leasePurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#leaseBuyout').val());
#     $('#rentPurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#rentBuyout').val());
#     $('#margin').val(($('#equipment-purchase-price').val() - $('#total-outcost').val()).toFixed(2));
#     updateEquipmentCommissions();
# }

# function updateRecommendColorSalesPrice(colorTonerPrice, servicePrice, monoPages, colorPages) {
#     if (colorPages === 0) {
#         $('#recommended-color-sales-price').html('0.0000');
#         $('#recommended-color-sales-price2').val(0);
#         $('#included-color-price').val(0);
#         $('#bundled-color-price').val(0);
#         return 0;
#     }

#     let colorSalesPrice = getRecommendColorSalesPrice(colorTonerPrice, servicePrice, monoPages, colorPages);
#     $('#recommended-color-sales-price').html(colorSalesPrice);
#     $('#recommended-color-sales-price2').val(colorSalesPrice);
#     $('#rent-recommended-color-sales-price2').val(colorSalesPrice);
#     if ( !$.trim($('#proposed-color-sales').val())) {
#         $('#proposed-color-sales').val(colorSalesPrice);
#     }

#     // pre-calculate base rate  (gel 2019-11-25)
#     if ( !$.trim($('#base-rate-color').val())) {
#         $('#base-rate-color').val(($('#proposed-color-sales').val() * page_cost_details.def_base_volume_color).toFixed(2));
#     }

#     $('#included-color-price').val(colorSalesPrice);
#     $('#bundled-color-price').val(colorSalesPrice);
#     $('#rent-bundled-color-price').val(colorSalesPrice);
#     return colorSalesPrice;
# }

# function updateRecommendColorTonerPrice(colorTonerMarginPrice, totalMonthlyColorPages, colorCoverage) {
#     // if service only, return 0
#     if (mgmtAsmpts.contract_service_type === 'service_only') {
#         $('#recommended-color-toner-price').html('0');
#         return 0;
#     }

#     let colorTonerPrice = getRecommendColorTonerPrice(colorTonerMarginPrice, totalMonthlyColorPages, colorCoverage);

#     // supplies only bump (GEL 2020-04-07)
#     if (mgmtAsmpts.contract_service_type === 'supplies_only') {
#         colorTonerPrice = (colorTonerPrice * (1 + mgmtAsmpts.supplies_only)).toFixed(4);
#     }

#     $('#recommended-color-toner-price').html(colorTonerPrice);
#     return colorTonerPrice;
# }

# function updateRecommendMonoSalesPrice(monoTonerPrice, servicePrice, monoPages, colorPages) {
#     if (monoPages === 0) {
#         $('#recommended-mono-sales-price').html('0.0000');
#         $('#recommended-mono-sales-price2').val(0);
#         $('#included-mono-price').val(0);
#         $('#bundled-mono-price').val(0);
#         $('#rent-recommended-mono-sales-price').html('0.0000');
#         $('#rent-recommended-mono-sales-price2').val(0);
#         $('#rent-bundled-mono-price').val(0);
#         return 0;
#     }

#     let monoSalesPrice = getRecommendMonoSalesPrice(monoTonerPrice, servicePrice, monoPages, colorPages);
#     $('#recommended-mono-sales-price').html(monoSalesPrice);
#     $('#recommended-mono-sales-price2').val(monoSalesPrice);
#     $('#rent-recommended-mono-sales-price2').val(monoSalesPrice);
#     if ( !$.trim($('#proposed-mono-sales').val())) {
#         $('#proposed-mono-sales').val(monoSalesPrice);
#     }

#     // pre-calculate base rate  (gel 2019-11-25)
#     if ( !$.trim($('#base-rate-mono').val())) {
#         $('#base-rate-mono').val(($('#proposed-mono-sales').val() * page_cost_details.def_base_volume_mono).toFixed(2));
#     }

#     $('#included-mono-price').val(monoSalesPrice);
#     $('#bundled-mono-price').val(monoSalesPrice);
#     $('#rent-bundled-mono-price').val(monoSalesPrice);
#     return monoSalesPrice;
# }

# function updateRecommendMonoTonerPrice(scaledTonerCPP, pages, monoCoverage) {
#     // service only = 0
#     if (mgmtAsmpts.contract_service_type === 'service_only') {
#         $('#recommended-mono-toner-price').html('0');
#         return 0;
#     }

#     let monoTonerPrice = getRecommendMonoTonerPrice(scaledTonerCPP, pages, monoCoverage);

#     // supplies only bump (GEL 2020-04-07)
#     if (mgmtAsmpts.contract_service_type === 'supplies_only') {
#         monoTonerPrice = (monoTonerPrice * (1 + mgmtAsmpts.supplies_only)).toFixed(4);
#     };

#     $('#recommended-mono-toner-price').html(monoTonerPrice);
#     return monoTonerPrice;
# }

# function updateRecommendMonthlyPrice(monoTonerPrice, colorTonerPrice, servicePrice) {
#     let monthlyPrice = (monoTonerPrice + colorTonerPrice + servicePrice).toFixed(4);
#     if (+monthlyPrice === 0) {
#         $('#recommended-monthly-price').html('0');
#         return 0;
#     }

#     $('#recommended-monthly-price').html(monthlyPrice);
#     return +monthlyPrice;       // return float instead of string
# }


def calculateMargin(request): 
    runningMonoColorPriceLocal = 0
    runningMonoColorCostLocal = 0
    runningColorPriceLocal = 0
    runningColorCostLocal = 0
    runningMonoPriceLocal = 0
    runningMonoCostLocal = 0

    # proposal service items
    p_objects = ProposalServiceItem.objects.all()

    # get whoever is logged in company or affiliated company
    mgmtAsmpts = ManagementAssumption.objects.get(company=company)
    
    for device in p_objects: 
        # only include network devices
        if device.is_non_network == True: 
            continue
        serviceCost = float(device.service_cost) * (1 - mgmtAsmpts.target_margin_service)
        totalPages = device.total_mono_pages - device.total_color_pages

        if device.is_color_device: 
            overage = device.total_color_pages - device.base_volume_color
            salesPrice = 0
            if (device.proposed_cpp_color > 0): 
                salesPrice = float(device.proposed_cpp_color)
            else: 
                salesPrice = float(device.rcmd_cpp_color)
            
            runningMonoColorPriceLocal += salesPrice * overage + float(device.base_rate_color);
            colorCost = float(device.color_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
            
            if(totalPages > 0): 
                runningColorCostLocal += colorCost + (serviceCost * device.total_color_pages / totalPages);
            else: 
                runningColorCostLocal += 0
        else: 
            overage = device.total_mono_pages - device.base_volume_mono;

            salesPrice = 0;
            if (device.proposed_cpp_mono > 0): 
                salesPrice = float(device.proposed_cpp_mono)
            else: 
                salesPrice = float(device.rcmd_cpp_mono)
            
            runningMonoPriceLocal += salesPrice * overage + float(device.base_rate_mono);
            monoCost = float(device.mono_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
            
            if(totalPages > 0): 
                runningMonoCostLocal += monoCost + (serviceCost * device.total_mono_pages / totalPages);
            else: 
                runningMonoCostLocal += 0

    if(runningMonoPriceLocal > 0): 
        monoMargin = round((runningMonoPriceLocal - runningMonoCostLocal) / runningMonoPriceLocal * 100);
    else: 
        monoMargin = 0
    
    if(runningMonoColorPriceLocal > 0): 
        monoColorMargin = round((runningMonoColorPriceLocal - runningMonoColorCostLocal) / runningMonoColorPriceLocal * 100);
    else: 
        monoColorMargin = 0
    
    if(runningColorPriceLocal > 0): 
        colorMargin = round((runningColorPriceLocal - runningColorCostLocal) / runningColorPriceLocal * 100);
    else: 
        colorMargin = 0

    pass

def equalizeMargin(changeType, device_id, proposal_id): 
    p_objects = ProposalServiceItem.objects.all()
    device = p_objects.filter(proposal_id=proposal_id).filter(printer_id=device_id)

    rm_price = float(device.rcmd_cpp_mono);
    rc_price = float(device.rcmd_cpp_color);
    tm_pages = device.total_mono_pages;
    tc_pages = device.total_color_pages;

    base_total = (rm_price * tm_pages) + (rc_price * tc_pages);

    pm_price = float(device.proposed_cpp_mono);
    pc_price = float(device.proposed_cpp_color);

    base_rate_mono = device.base_volume_mono * pm_price
    base_rate_color = device.base_volume_color * pc_price

    pass
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

def getRecommendMonoSalesPrice(monoTonerPrice, servicePrice, monoPages, colorPages):
    # format .4
    rcmd_mono_sales_price = float((monoTonerPrice + (servicePrice * monoPages / (monoPages + colorPages))) / monoPages);
    return rcmd_mono_sales_price

def getRecommendServicePrice(serviceBumpedMarginPrice, totalMonthlyPages):  
    # format .4
    rcmd_service_price = float(serviceBumpedMarginPrice * totalMonthlyPages);
    return rcmd_service_price
    
def selectAccessory(devRow, accRow, accId):
    # acc = accessories[accId];
    # quantity = parseInt($('#networkDevice-quantity').val());
    # outCost = acc.out_cost * (1 + mgmtAsmpts.accessory_inflate) * quantity;
    # msrp = acc.msrp_cost * quantity;
    # $('#acc-out' + devRow + accRow).val(parseFloat(outCost).toFixed(2));
    # $('#acc-msrp' + devRow + accRow).val(parseFloat(msrp).toFixed(2));
    # updateDeviceTotalCosts(devRow); 
    pass
def selectPurchaseDevice(dropdown, rowNum): 
    pass
def updateRecommendServicePrice(request,serviceBumpedMarginPrice, totalMonthlyPages): 
    # supply only = 0
    mgmtAsmpts = ManagementAssumption.objects.get(company=company)
    if (mgmtAsmpts.contract_service_type == 'supplies_only' or serviceBumpedMarginPrice == 0 or totalMonthlyPages == 0):
        return 0;
    
    servicePrice = getRecommendServicePrice(serviceBumpedMarginPrice, totalMonthlyPages);
    return servicePrice;

def updateDeviceTotalCosts(request, prop_id, pid): 
    proposal = Proposal.objects.get(pk=prop_id)
    device = PrinterCost.objects.filter(product_id=pid)

    mgmtAsmpts = ManagementAssumption.objects.get(pk=proposal.management_assumptions_id)
    p_objects = ProposalPurchaseItem.objects.filter(proposal_id=proposal.id)
    
    accOut = 0.0
    accMsrp = 0.0

    for device in p_objects: 
        accOut += device.out_cost
        accMsrp += device.msrp_cost
    
    dOut = float(device.out_cost);
    dMsrp = float(device.msrp_cost);
    
    # format .2
    total_outcost = float(dOut + accOut);
    total_msrpcost = float(dMsrp + accMsrp);
    
    equipment_purchase_price = total_outcost / (1 - mgmtAsmpts.target_margin_equipment);
    overall_margin = updateOverallMargin();
    pass

def updateOverallMargin(): 
    # $('#margin').val(($('#equipment-purchase-price').val() - $('#total-outcost').val()).toFixed(2));
    # $('#margin-percentage').val(($('#margin').val() / $('#equipment-purchase-price').val() * 100).toFixed(2));
    # if($('#leaseBuyout').val()===""){
    #     $('#leaseBuyout').val(0);
    # }    
    # if($('#rentBuyout').val()===""){
    #     $('#rentBuyout').val(0);
    # }   
    # if($('#equipment-purchase-price').val()===""){
    #     $('#equipment-purchase-price').val(0);
    # }
    # $('#leasePurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#leaseBuyout').val());
    # $('#rentPurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#rentBuyout').val());
    # updateEquipmentCommissions();
    pass

def updateEquipmentCommissions(deviceType): 
    # let NetEquipmentCommission = 0;

    # switch (mgmtAsmpts.eq_commission_type) {
    #     case 'eq_flat_margin':
    #         NetEquipmentCommission = mgmtAsmpts.eq_percent_margin_flat_rate * $('#margin').val();
    #         $('#eqcommission').html(`${NetEquipmentCommission.toFixed(2)}`);
    #         break;
    #     case 'eq_flat_revenue':
    #         NetEquipmentCommission = mgmtAsmpts.eq_percentage_revenue_flat_rate * $('#equipment-purchase-price').val();
    #         $('#eqcommission').html(`${NetEquipmentCommission.toFixed(2)}`);
    #         break;
    #     case 'eq_blended_margin':
    #         NetEquipmentCommission = (deviceType == 'printer' ? mgmtAsmpts.eq_margin_rate_printers : mgmtAsmpts.eq_margin_rate_copiers) * $('#margin').val();
    #         $('#eqcommission').html(`${NetEquipmentCommission.toFixed(2)}`);
    #         break;
    #     case 'eq_blended_revenue':
    #         NetEquipmentCommission = (deviceType == 'printer' ? mgmtAsmpts.eq_revenue_rate_printers : mgmtAsmpts.eq_revenue_rate_copiers) * $('#equipment-purchase-price').val();
    #         $('#eqcommission').html(`${NetEquipmentCommission.toFixed(2)}`);
    #         break;
    #     default:
    
    # }
    pass