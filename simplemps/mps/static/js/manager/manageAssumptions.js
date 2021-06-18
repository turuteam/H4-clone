$(document).ready(function () {
    showHideInputs();
});

$('#commissionSelect').change(function () {
    showHideInputs();
});

function showHideInputs() {
    switch($('#commissionSelect').val()) {
        case 'flat_margin':
            $('#flatPrintInputs').removeClass('hide');
            $('#marginFlatLabel').removeClass('hide');
            $('#marginFlatRate').removeClass('hide');
            $('#revenueFlatLabel').addClass('hide');
            $('#revenueFlatRate').addClass('hide');

            $('#blendedPrinterInputs').addClass('hide');
            $('#blendedCopierInputs').addClass('hide');
            break;
        case 'flat_revenue':
            $('#flatPrintInputs').removeClass('hide');
            $('#marginFlatLabel').addClass('hide');
            $('#marginFlatRate').addClass('hide');
            $('#revenueFlatLabel').removeClass('hide');
            $('#revenueFlatRate').removeClass('hide');

            $('#blendedPrinterInputs').addClass('hide');
            $('#blendedCopierInputs').addClass('hide');
            break;
        case 'blended_margin':
            $('#flatPrintInputs').addClass('hide');
            $('#blendedPrinterInputs').removeClass('hide');
            $('#marginRateOnPrinters').removeClass('hide');
            $('#revenueRateOnPrinters').addClass('hide');

            $('#blendedCopierInputs').removeClass('hide');
            $('#marginRateOnCopiers').removeClass('hide');
            $('#revenueRateOnCopiers').addClass('hide');
            break;
        case 'blended_revenue':
            $('#flatPrintInputs').addClass('hide');

            $('#blendedPrinterInputs').removeClass('hide');
            $('#marginRateOnPrinters').addClass('hide');
            $('#revenueRateOnPrinters').removeClass('hide');

            $('#blendedCopierInputs').removeClass('hide');
            $('#marginRateOnCopiers').addClass('hide');
            $('#revenueRateOnCopiers').removeClass('hide');
            break;
    }
}

$(document).ready(function () {
    showHideInputs2();
});

$('#eqcommissionSelect').change(function () {
    showHideInputs2();
});

function showHideInputs2() {
    switch($('#eqcommissionSelect').val()) {
        case 'eq_flat_margin':
            $('#eqflatPrintInputs').removeClass('hide');
            $('#eqmarginFlatLabel').removeClass('hide');
            $('#eqmarginFlatRate').removeClass('hide');
            $('#eqrevenueFlatLabel').addClass('hide');
            $('#eqrevenueFlatRate').addClass('hide');

            $('#eqblendedPrinterInputs').addClass('hide');
            $('#eqblendedCopierInputs').addClass('hide');
            break;
        case 'eq_flat_revenue':
            $('#eqflatPrintInputs').removeClass('hide');
            $('#eqmarginFlatLabel').addClass('hide');
            $('#eqmarginFlatRate').addClass('hide');
            $('#eqrevenueFlatLabel').removeClass('hide');
            $('#eqrevenueFlatRate').removeClass('hide');

            $('#eqblendedPrinterInputs').addClass('hide');
            $('#eqblendedCopierInputs').addClass('hide');
            break;
        case 'eq_blended_margin':
            $('#eqflatPrintInputs').addClass('hide');

            $('#eqblendedPrinterInputs').removeClass('hide');
            $('#eqmarginRateOnPrinters').removeClass('hide');
            $('#eqrevenueRateOnPrinters').addClass('hide');

            $('#eqblendedCopierInputs').removeClass('hide');
            $('#eqmarginRateOnCopiers').removeClass('hide');
            $('#eqrevenueRateOnCopiers').addClass('hide');
            break;
        case 'eq_blended_revenue':
            $('#eqflatPrintInputs').addClass('hide');

            $('#eqblendedPrinterInputs').removeClass('hide');
            $('#eqmarginRateOnPrinters').addClass('hide');
            $('#eqrevenueRateOnPrinters').removeClass('hide');

            $('#eqblendedCopierInputs').removeClass('hide');
            $('#eqmarginRateOnCopiers').addClass('hide');
            $('#eqrevenueRateOnCopiers').removeClass('hide');
            break;
    }
}

$('#save').on('click', function () {
    let dat = {
        // supplies
        'target_margin_toner' : $('#targetMarginToner').val() / 100,
        'effective_mono_yield' : $('#effectiveMonoYield').val() / 100,
        'effective_color_yield' : $('#effectiveColorYield').val() / 100,
        'reman_rebate' : $('#remanRebate').val(),
        'oem_smp_rebate' : $('#smpRebate').val(),
        'oem_rebate' : $('#oemRebate').val(),
        'toner_shipping_price' : $('#shippingOnToner').val(),
        'distro_markup' : $('#distroMarkup').val() / 100,
        'supplies_only' : $('#suppliesOnly').val() / 100,
        'cpc_toner_only' : Boolean(parseInt($('#changeCPCTonerOnly').val())),
        // non network
        'annual_mono_cartridges' : $('#annualMonoCartridges').val(),
        'maintenance_kit_replaced_years' : $('#kitReplacedAge').val(),
        'percentage_color' : $('#percentageColor').val(),
        'non_network_margin' : $('#nonNetworkDeviceMargin').val(),
        // commissions
        'commission_type' : $('#commissionSelect').val(),
        'percent_margin_flat_rate' : $('#marginFlatRate').val() / 100,
        'percentage_revenue_flat_rate' : $('#revenueFlatRate').val() / 100,
        'margin_rate_printers' : $('#marginRateOnPrinters').val() / 100,
        'margin_rate_copiers' : $('#marginRateOnCopiers').val() / 100,
        'revenue_rate_printers' : $('#revenueRateOnPrinters').val() / 100,
        'revenue_rate_copiers' : $('#revenueRateOnCopiers').val() / 100,
        'pay_non_network_commission' : Boolean(parseInt($('#payNonNetworkCommission').val())),
        // service
        'target_margin_service' : $('#targetMarginService').val() / 100,
        'gold_service' : $('#goldService').val() / 100,
        'platinum_service' : $('#platinumService').val() / 100,
        'service_only' : $('#serviceOnly').val() / 100,
        'inflate_older_than' : $('#inflateAge').val(),
        'old_inflate_percent' : $('#inflateAgePercent').val() / 100,
        'inflate_out_of_area' : $('#inflateOOAZ1').val() / 100,
        'tier2_inflate' : $('#inflateOOAZ2').val() / 100,
        'tier3_inflate' : $('#inflateOOAZ3').val() / 100,
        // equipment
        'target_margin_equipment' : $('#targetMarginEquipment').val() / 100,        
        'equipment_inflate' : $('#equipmentInflate').val() / 100,
        'accessory_inflate' : $('#accessoryInflate').val() / 100,
        // equipment commissions
        'eq_commission_type' : $('#eqcommissionSelect').val(),
        'eq_percent_margin_flat_rate' : $('#eqmarginFlatRate').val() / 100,
        'eq_percentage_revenue_flat_rate' : $('#eqrevenueFlatRate').val() / 100,
        'eq_margin_rate_printers' : $('#eqmarginRateOnPrinters').val() / 100,
        'eq_margin_rate_copiers' : $('#eqmarginRateOnCopiers').val() / 100,
        'eq_revenue_rate_printers' : $('#eqrevenueRateOnPrinters').val() / 100,
        'eq_revenue_rate_copiers' : $('#eqrevenueRateOnCopiers').val() / 100,
        // misc
        'toner_after_reman' : $('#tonerAfterReman').val(),
        'toner_after_oem_smp' : $('#tonerAfterSMP').val(),
        'min_mono_margin' : $('#minMonoMargin').val() / 100,
        'min_color_margin' : $('#minColorMargin').val() / 100,
        'min_mono_on_color_margin' : $('#minMonoOnColorMargin').val() / 100,
        'change_device_price_base' : Boolean(parseInt($('#changeDevicePriceBase').val())),
        'managed_cartridge_inflate' : $('#managedCartridgeInflate').val() / 100,    
        // features
        'allow_cartridge_pricing' : Boolean(parseInt($('#changeCPCOption').val())),
        'allow_leasing' : Boolean(parseInt($('#changeLeasingOption').val())),
        'allow_rental' : Boolean(parseInt($('#changeRentalOption').val())),
        'allow_reman' : Boolean(parseInt($('#changeRemanOption').val())),
        'allow_tiered' : Boolean(parseInt($('#changeTieredOption').val())),
        'allow_term_offsets' : Boolean(parseInt($('#changeTermOffsetOption').val())),
        'allow_tco' : Boolean(parseInt($('#changeTCOOption').val())),
        'allow_flat_rate' : Boolean(parseInt($('#changeFlatRateOption').val())),
        // contract term cost management (offsets based on duration)
        'cost_offset_12month' : $('#offset12Month').val() / 100,
        'cost_offset_24month' : $('#offset24Month').val() / 100,
        'cost_offset_36month' : $('#offset36Month').val() / 100,
        'cost_offset_48month' : $('#offset48Month').val() / 100,
        'cost_offset_60month' : $('#offset60Month').val() / 100
    };

    $.ajax({
        type: 'POST',
        cache: false,
        data: {
            'assumption_data': JSON.stringify(dat)
        },
        url: '/manageAssumptions/update'
    }).done(function (response) {
        alert('Assumption data saved!');
    }).fail(function (response) {
        alert(response);
    });
});