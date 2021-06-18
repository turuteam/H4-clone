'use strict';
/*global p_objects*/
/*global mgmtAsmpts*/
/*global proposal_service_items*/
/*global proposal_purchase_items*/
/*global monoMargin*/
/*global monoColorMargin*/
/*global colorMargin*/
/*global minNetMargin*/
/*global addThousandsSeparator*/
/*global isNullOrWhitespace*/

let printer_costs;
let printer_details;
let toner_costs;
let accessories;
let non_network_details;
let deviceShortName;
let deviceMakeName;
let proposal_id;
let proposal_term;
let company_id;
let network_devices = [];
let non_network_devices = [];
let network_table;
let non_network_table;
let allow_leasing;
let allow_rental;
let modal_mode;
let page_cost_details;
let proposal_settings;

// leasing variables.
let token;
let cache = {};

// calculation variables
let runningMonoPrice = 0;
let runningMonoColorPrice = 0;
let runningColorPrice = 0;
let runningMonoCost = 0;
let runningColorCost = 0;
let runningMonoColorCost = 0;

let saveEquipment = false;

let leasingCompanies = [];

// margin variables
var monoMargin = 0;
var monoColorMargin = 0;
var colorMargin = 0;

$(document).ready(function () {
    proposal_id = mgmtAsmpts.proposal_id;
    // toggle leasing on/off based on managment assumptions  (GEL 2019-08-31)
    if (mgmtAsmpts.allow_leasing) {
        $('#open-lease-options').show();
    } else {
        $('#open-lease-options').hide();
        $("#buy-lease option[value='lease']").remove();
    }; 
        // toggle rental on/off based on managment assumptions  (GEL 2020-05-17)
    if (mgmtAsmpts.allow_rental) {
        $('#open-rent-options').show();
    } else {
        $('#open-rent-options').hide();
        $("#buy-lease option[value='rent']").remove();
    }; 
    // toggle tiered pricing on/off based on managment assumptions  (GEL 2019-08-31)
    if (mgmtAsmpts.allow_tiered) {
        $('#tiered-button').show();
    } else {
        $('#tiered-button').hide();
    };
    // toggle price per cartridge on/off based on management assumptions (GEL 2019-09-11)
    if (mgmtAsmpts.allow_cartridge_pricing) {
        $('#ppc-button').show();
    } else {
        $('#ppc-button').hide();
    };
    // toggle flat rate display on/off based on managment assumptions  (GEL 2020-03-17)
    if (mgmtAsmpts.allow_flat_rate) {
        $('#flat-rate-button').show();
    } else {
        $('#flat-rate-button').hide();
    };

    // retrieve global proposal settings
    proposal_settings = loadProposalSettings(mgmtAsmpts.proposal_id);
    company_id = proposal_settings.company_id;
    proposal_term = proposal_settings.term;
    $('#rental-company-id').val(company_id);
    $('#leasing-company-id').val(company_id);

    deviceShortName = $('#networkDevice-shortName').val();
    deviceMakeName = $('#networkDevice-makeName').val();

    network_table = $('#network-devices-table').DataTable({
        'searching':false,
        'pageLength': 10,
        'lengthChange': false,
        'columnDefs': [{ 'orderable': false, 'targets': 12}]
    });
    non_network_table = $('#non-network-devices-table').DataTable({
        'searching':false,
        'pageLength': 10,
        'lengthChange': false,
        'columnDefs': [{ 'orderable': false, 'targets': 3}]
    });
    $('#network-devices-table').addClass('network-table').addClass('size-14');
    $('#non-network-devices-table').addClass('non-network-table').addClass('size-14');

    console.log("NOW", proposal_service_items)

    for (let i = 0; i < proposal_service_items.length; i++) {
        let item = proposal_service_items[i];
        if (isNaN(item.proposal_purchase_item_id)) {
            item.proposal_purchase_item_id = null;
        };
        console.log("KEATON", item)
        if (item['is_non_network']) {
            appendToNonNetworkTable(item);
        } else {
            appendToNetworkTable(item, item.proposal_purchase_item_id);
        }
    }

    $('#network-devices-table_wrapper')
        .find('div.row.grid-x')
        .find('.small-6.columns.cell')
        .toggleClass('small-6 small-12')
        .addClass('data_table_wrapper')
        .css({
            'color': 'white'
        });

    $('#non-network-devices-table_wrapper')
        .find('div.row.grid-x')
        .find('.small-6.columns.cell')
        .toggleClass('small-6 small-12')
        .addClass('data_table_wrapper')
        .css({
            'color': 'white'
        });

    [network_table, non_network_table].forEach(table => {
        $(table.table().body()).on('click', 'tr td button[data-type="remove-device"]', function () {
            let row = $(this).parents('tr');
            let id = row.data('id') || $('.parent').data('id');
            
            row = table.row(row);

            let parent = $(this).closest('tr');
            if($(parent).hasClass('child'))
                location.reload(); 
                
            $.ajax({
                type: 'POST',
                cache: false,
                data: { id: id },
                url: window.location.origin + '/proposal/removeNetworkDevice/' + proposal_id + '/'
            }).done(function () {
                row.remove().draw();
                
                $(`tr[data-id="${id}"]`).remove();
                
                ['bw1', 'bw2', 'bw3', 'bw4', 'color1', 'color2', 'color3'].forEach(tier => {
                    toggle_dummy_row(tier);
                    if ($(`table#${tier} > tbody > .dummy-row`).length > 1) {
                        remove_dummy_row(tier);
                        add_dummy_row(tier);
                    }
                });
                if (p_objects[id].mono_tier) {
                    footerCalculate(p_objects[id].mono_tier, update_row_in_summary_table);
                }
                if (p_objects[id].color_tier) {
                    footerCalculate(p_objects[id].color_tier, update_row_in_summary_table);
                }
                delete p_objects[id];
                $(proposal_service_items).each(function(index, item) {
                    if (item.id === id) {
                        let purchase_item_id = proposal_service_items[index].proposal_purchase_item_id
                        $(proposal_purchase_items).each(function(index, purchase_item) {
                            if (purchase_item.id === purchase_item_id) {
                                proposal_purchase_items.splice(index, 1);
                            }
                        });
                        proposal_service_items.splice(index, 1)
                    }
                });
                costPerCartridgeTable.row(".id-"+id).remove().draw();
                FlatRaceTable.row(".id-"+id).remove().draw();

                updateSummaryAndMonthly();
            }).fail(function () {
                alert('failed to remove non-network device');
            })
        });

        
    });

    $('.btn-previous').click(function () {
        window.location.href = window.location.origin + '/proposal/details/' + proposal_id;
    });
    updateSummaryAndMonthly();
    loadMakeDetails();

    // add event to detect change in Make then reload shortName dropdown
    $('#networkDevice-makeName').on('change', function() {loadPrinterDetailsByMake()});
    $('#nonNetworkDevice-makeName').on('change', function() {loadPrinterDetailsByMakeNN()});

    loadPrinterDetails();

    // leasing
    // authenticate();
    getLeasingData();
    getRentalData();

    $('#add-device-network').on('click', function() {
        modal_mode = 'new';
        resetNetworkDeviceModal();
        $('#addNetworkDevice').foundation('open');
    });

    allow_leasing = mgmtAsmpts.allow_leasing;
    allow_rental = mgmtAsmpts.allow_rental;
    // update modal UI as data is entered/edited
    $('#addNetworkDevice .reactive').on('input', updateModalUI);
});

function setMonoCPP() {
    const monoCoverage = $('#mono-coverage').val();
    const colorCoverage = $('#color-coverage').val();

    let monoCpp = 0;
    if (mgmtAsmpts.contract_service_type == 'service_only') {
        monoCpp = (parseFloat(toner_costs.scaled_service_cost) * (1-mgmtAsmpts.target_margin_service)) * (monoCoverage / 0.05)
    } else if (mgmtAsmpts.contract_service_type == 'supplies_only') {
        monoCpp = parseFloat(toner_costs.raw_mono_cost) * (monoCoverage / 0.05)
    } else {
        monoCpp =((parseFloat(toner_costs.scaled_service_cost) * (1-mgmtAsmpts.target_margin_service)) + parseFloat(toner_costs.raw_mono_cost)) * (monoCoverage / 0.05)
    }

    $('#raw-mono-cpp').text(`$${(monoCpp + '').substring(0,6)}`);
}

function setColorCPP() {
    const monoCoverage = $('#mono-coverage').val();
    const colorCoverage = $('#color-coverage').val();

    let colorCpp = 0;
    if (mgmtAsmpts.contract_service_type == 'service_only') {
        
        colorCpp = (parseFloat(toner_costs.scaled_service_cost) * (1-mgmtAsmpts.target_margin_service)) * (colorCoverage / 0.05)
    } else if (mgmtAsmpts.contract_service_type == 'supplies_only') {
        
        colorCpp = (parseFloat(toner_costs.raw_color_cost))
    } else {
        colorCpp = ((parseFloat(toner_costs.scaled_service_cost) * (1-mgmtAsmpts.target_margin_service)) + (parseFloat(toner_costs.raw_color_cost))) * (colorCoverage / 0.05)
    }
    $('#raw-color-cpp').text(`${(colorCpp + '').substring(0,6)}`);
}

async function updateModalUI() {
    const pageInfo = {
        monoMonthly: parseInt($('#total-monthly-mono-pages').val()) || 0,
        colorMonthly: parseInt($('#total-monthly-color-pages').val()) || 0,
        monoCoverage: parseFloat($('#mono-coverage').val()) || 0,
        colorCoverage: parseFloat($('#color-coverage').val()) || 0
    }
    pageInfo.totalMonthly =  pageInfo.monoMonthly + pageInfo.colorMonthly;
    $('#total-monthly-pages').val(pageInfo.totalMonthly);

    const recommendedPrice = {
        monoToner: updateRecommendMonoTonerPrice(toner_costs.scaled_mono_cost, pageInfo.monoMonthly, pageInfo.monoCoverage),
        monoCPP: updateMonoCPP(toner_costs.raw_mono_cost, toner_costs.scaled_service_cost, pageInfo.monoCoverage),
        colorToner: updateRecommendColorTonerPrice(toner_costs.scaled_color_cost, pageInfo.colorMonthly, pageInfo.colorCoverage),
        service: updateRecommendServicePrice(toner_costs.scaled_service_cost, pageInfo.totalMonthly),
    };
    
    recommendedPrice.monoSales =  updateRecommendMonoSalesPrice(recommendedPrice.monoToner, recommendedPrice.service, pageInfo.monoMonthly, pageInfo.colorMonthly);
    recommendedPrice.monoCPP = updateMonoCPP(recommendedPrice.monoCPP);
    console.log('raw mono toner', toner_costs.raw_mono_cost);
    console.log('scaled mono toner', toner_costs.scaled_mono_cost);
    console.log('raw color toner', toner_costs.raw_color_cost);
    console.log('scaled color toner', toner_costs.scaled_color_cost);
    console.log('raw service', toner_costs.scaled_service_cost * (1-mgmtAsmpts.target_margin_service));
    console.log('scaled service', toner_costs.scaled_service_cost);
    console.log('mono cpp', recommendedPrice.monoCPP);
    recommendedPrice.colorSales = updateRecommendColorSalesPrice(recommendedPrice.colorToner, recommendedPrice.service, pageInfo.monoMonthly, pageInfo.colorMonthly);
    recommendedPrice.monthly = updateRecommendMonthlyPrice(recommendedPrice.monoToner, recommendedPrice.colorToner, recommendedPrice.service);

    // got to set the ppc pricing here on update for the modal.
    if(proposal_settings.proposal_type == 'ppc') {
        await getSelfServicePPCMonoPrice();
        await getSelfServicePPCColorPrice();
        // recommendedPrice.recommended_cost_per_cartridge_mono = await getSelfServicePPCMonoPrice();
        // recommendedPrice.recommended_cost_per_cartridge_color = await getSelfServicePPCColorPrice(); 
    }

    const proposedPrice = {
        baseMonoVolume: parseInt($('#base-volume-mono').val()) || 0,
        baseColorVolume: parseInt($('#base-volume-color').val()) || 0,
        baseMonoRate: parseFloat($('#base-rate-mono').val()) || 0,
        baseColorRate: parseFloat($('#base-rate-color').val()) || 0,
        monoSalesPrice: parseFloat($('#proposed-mono-sales').val()) || 0,
        colorSalesPrice: parseFloat($('#proposed-color-sales').val()) || 0,
    };

    let device_type;
    const id = $('add-network-device').data('id');

    if (id) {
        device_type = p_objects[id].service.device_type
    } else if (printer_details !== undefined) {
        device_type = printer_details.device_type;
    }

    // if margin locked, see if proposed pricing need to be adjusted  (gel 2019-11-25)
    // otherwise just save any possible changes in case switch is changed back
    if($('#lock-margin').val() == '1') {
        let changeType = "unknown";
        equalizeMargin(changeType);             
    } else {
        $('#saved-mono-sales').val($('#proposed-mono-sales').val());
        $('#saved-color-sales').val($('#proposed-color-sales').val());
    }

    if (device_type) {
        updateNetDeviceCommission(device_type, pageInfo, recommendedPrice, proposedPrice);
    }
}

$('#included-monthly-mono-pages').attr('title', 'Enter the mono billed pages over the life of the lease to include in the raw purchase price.  This also resets bundled mono page count on bundled cpp leases.');
$('#included-monthly-color-pages').attr('title', 'Enter the color billed pages over the life of the lease to include in the raw purchase price.  This also resets bundled color pages on bundled cpp leases.');

// perhaps not on change, depending on how api works for short model name search
$('#networkDevice-shortName').on('change', function () {
    // When a model is changed, force all values to default   (GEL 12/29/2019)
    $('#networkDevice-quantity').val('1');
    $('#networkDevice-totalOutcost').val('');
    $('#networkDevice-totalOutcost').prop('disabled', true);
    $('#networkDevice-purchasePrice').val('');
    $('#networkDevice-purchasePrice').prop('disabled', true);
    $('#total-monthly-mono-pages').val('');
    $('#total-monthly-color-pages').val('');
    $('#total-monthly-pages').val('');
    $('#mono-coverage').val('.05');
    $('#color-coverage').val('.05');
    $('#color-coverage').prop('disabled', true);
    $('#recommended-mono-toner-price').html('0');
    $('#recommended-color-toner-price').html('0');
    $('#recommended-service-price').html('0');
    $('#recommended-monthly-price').html('0');
    $('#recommended-mono-sales-price').html('0.0000');
    $('#recommended-color-sales-price').html('0.0000');
    $('#self-service-mono-price').html('0.00');
    $('#self-service-color-price').html('0.00');
    $('#retail-mono-price').html('0.00');
    $('#retail-color-price').html('0.00');
    $('#raw-mono-cpp').html('0.0000');
    $('#raw-color-cpp').html('0.0000');
    // lease section
    $('#included-monthly-mono-pages').val(0);
    $('#included-monthly-color-pages').val(0);
    $('#included-mono-price').val(0);
    $('#included-color-price').val(0);
    $('#included-mono-monthly').val(0);
    $('#included-color-monthly').val(0);
    $('#includedAmt').val(0);
    $('#bundled-monthly-mono-pages').val('');
    $('#bundled-monthly-color-pages').val('');
    $('#recommended-mono-sales-price2').val(0);
    $('#recommended-color-sales-price2').val(0);
    $('#bundled-mono-price').val(0);
    $('#bundled-color-price').val(0);
    $('#bundled-mono-monthly').val(0);
    $('#bundled-color-monthly').val(0);
    $('#bundledAmt').val(0);
    // rental section
    $('#rent-bundled-monthly-mono-pages').val('');
    $('#rent-bundled-monthly-color-pages').val('');
    $('#rent-recommended-mono-sales-price2').val(0);
    $('#rent-recommended-color-sales-price2').val(0);
    $('#rent-bundled-mono-price').val(0);
    $('#rent-bundled-color-price').val(0);
    $('#rent-bundled-mono-monthly').val(0);
    $('#rent-bundled-color-monthly').val(0);
    $('#rent-bundledAmt').val(0);
    // end lease-rental sections
    $('#base-volume-mono').val('');
    $('#base-volume-color').val('');
    $('#base-volume-color').prop('disabled', true);
    $('#base-rate-mono').val('');
    $('#base-rate-color').val('');
    $('#base-rate-color').prop('disabled', true);
    $('#proposed-mono-sales').val('');
    $('#proposed-color-sales').val('');
    $('#commission').html('0.00');
    // end (GEL 12/29/2019)
    $('#equipment-options').prop('disabled', false);
    // transfer pages (GEL 02/10/2020)
    $('#transferButton').addClass('hide');

    if ($(this).val() !== '-1') {
        getNetDeviceDetails($(this).val());
    }
    $('#add-network-device').removeAttr('disabled');
    $('#equipment-options-title').html(this.options[this.selectedIndex].innerHTML);
    $('#transfer-pages-options-title').html(this.options[this.selectedIndex].innerHTML);

    // clear any previous equipment options
    clearEquipmentOptionsValues();
});

$('#equipment-purchase-price').keyup(function () {
    updateOverallMargin();
    updateEquipmentCommissions();
});

$('#margin').change(function () {
    updateMargin();
    updateEquipmentCommissions();
});

$('#margin-percentage').change(function () {
    updatePercent();
    updateEquipmentCommissions();
});

$('#equipment-purchase-price').change(function () {
    $(this).val(parseFloat(this.value).toFixed(2));
    $('#leasePurchasePrice').val(this.value);
    $('#rentPurchasePrice').val(this.value);
});

// Allow users to include the equipment cost into the CPP  (GEL 05-28-2020)
$('#changePurchaseOption').on('change', function () {
    if (printer_details.printer_is_color_type == true) {
        $('#price-in-color').removeClass('hide');
    } else {
        $('#price-in-color').addClass('hide');
    };

    if ($('#changePurchaseOption').val() == 1) {
        let monthlycost = $('#equipment-purchase-price').val()*1.1 / proposal_term;
        let monopages = $('#total-monthly-mono-pages').val()*1;
        let colorpages = $('#total-monthly-color-pages').val()*1;
        let monorevenue = monopages * $('#proposed-mono-sales').val()*1;
        let colorrevenue = colorpages * $('#proposed-color-sales').val()*1;
        let monopercent = monorevenue / (monorevenue + colorrevenue);
        let colorpercent = colorrevenue / (monorevenue + colorrevenue);
        let newCPPmono = $('#proposed-mono-sales').val()*1+(monthlycost * monopercent) / monopages;
        let newCPPcolor = $('#proposed-color-sales').val()*1+(monthlycost * colorpercent) / colorpages;
        $('#priceInCPPSection').removeClass('hide');
        $('#open-lease-options').prop('disabled', true);
        $('#open-rent-options').prop('disabled', true);
        $('#price-in-cpp-mono').val(newCPPmono.toFixed(4));
        $('#price-in-cpp-color').val(newCPPcolor.toFixed(4));
    } else {
        $('#priceInCPPSection').addClass('hide');
        $('#open-lease-options').prop('disabled', false);
        $('#open-rent-options').prop('disabled', false);
        $('#price-in-cpp-mono').val('0.00');
        $('#price-in-cpp-color').val('0.00');
    };
});

// recalculate lease purchase price (GEL 05-29-2020)
$('#leaseBuyout').on('change keyup', function () {
    let equipprice = $('#equipment-purchase-price').val()*1;
    let monthlymono = $('#included-mono-monthly').val()*1;
    let monthlycolor = $('#included-color-monthly').val()*1;
    let leaseterm = $('#lease-term option:selected').val()*1;
    let leasebuyout = $('#leaseBuyout').val()*1;
    let newpurchaseprice = equipprice + leasebuyout + leaseterm * (monthlymono + monthlycolor); 
    $('#leasePurchasePrice').val(newpurchaseprice.toFixed(2));
    calculateLeasePayment();
});

$('#save-new-network-device').on('click', function () {
    // save data flag
    saveEquipment = true;
    // Equipment cost included in CPP
    if ($('#changePurchaseOption').val() == 1) {
        $('#proposed-mono-sales').val($('#price-in-cpp-mono').val());
        $('#proposed-color-sales').val($('#price-in-cpp-color').val());
        $('#equipment-purchase-price').val('0.00')
    } 
    // end 
    $('#networkDevice-totalOutcost').val($('#total-outcost').val());
    $('#networkDevice-purchasePrice').val($('#equipment-purchase-price').val());
    $('#leasePurchasePrice').val($('#equipment-purchase-price').val());
    $('#rentPurchasePrice').val($('#equipment-purchase-price').val());
    // Update Total Monthly counts to reflect pages bundled in lease (GEL 06-20-2020)
    $('#total-monthly-mono-pages').val($('#total-monthly-mono-pages').val()*1-$('#included-monthly-mono-pages').val()*1);
    $('#total-monthly-color-pages').val($('#total-monthly-color-pages').val()*1-$('#included-monthly-color-pages').val()*1);
    $('#total-monthly-pages').val($('#total-monthly-mono-pages').val()*1+$('#total-monthly-color-pages').val()*1);

    $('#purchashEquipment').foundation('close');
});

$('#open-lease-options').on('click', function () {
    $('#leaseSelectType').val('1').prop('selected', true);
    $('#bundledAmt').val(0);
    calculateLeasePayment();
    $('#leasingOptions').foundation('open');
});

$('#save-leasing-options').on('click', function () {
    // save data flag
    saveEquipment = true;
    $('#buy-lease').val('lease');
    $('#leasingOptions').foundation('close');
});

// add Rent option (gel 05-15-2020)
$('#open-rent-options').on('click', function () {
    calculateRentPayment();
    $('#rentOptions').foundation('open');
});

$('#save-rent-options').on('click', function () {
    // save data flag
    saveEquipment = true;
    $('#buy-lease').val('rent');
    $('#rentOptions').foundation('close');
});


$('#add-network-device').on('click', function () {
    // add new network device into table, keys in the object match those in the database (besides equipment which needs to be added eventually!)

    let id = $(this).data('id');
    if (id) {
        let url = '/api/proposal-service-items/' + id + '/'

        let selector = `#network-devices-table tr[data-id="${id}"]`;

        const row = network_table.row(selector);
        let data = row.data();

        $.ajax({
            method: 'PATCH',
            url: url,
            headers: {
              "X-CSRFTOKEN": csrftoken
            },
            data: {
              number_printers_serviced: $('#networkDevice-quantity').val() || 1,
              rcmd_cpp_mono: proposal_settings.proposal_type !== 'ppc' ? $('#recommended-mono-sales-price').text() : $('#proposed-mono-sales').val(),
              rcmd_cpp_color: proposal_settings.proposal_type !== 'ppc' ? $('#recommended-color-sales-price').text() : $('#proposed-color-sales').val(),
              proposed_cpp_mono: $('#proposed-mono-sales').val(),
              proposed_cpp_color: $('#proposed-color-sales').val(),
              calculated_cpp_mono: $('#raw-mono-cpp').text().substring(1),
              calculated_cpp_color: $('#raw-color-cpp').text().substring(1),
              base_volume_mono: parseInt($('#base-volume-mono').val()) || 0,
              base_volume_color: parseInt($('#base-volume-color').val()) || 0,
              base_rate_mono: $('#base-rate-mono').val() || 0,
              base_rate_color: $('#base-rate-color').val() || 0,
              total_mono_pages: parseInt($('#total-monthly-mono-pages').val()) || 0,
              total_color_pages: parseInt($('#total-monthly-color-pages').val()) || 0,
              mono_coverage: $('#mono-coverage').val(),
              color_coverage: $('#color-coverage').val(),
              mono_toner_price: $('#recommended-mono-toner-price').text(),
              color_toner_price: $('#recommended-color-toner-price').text(),
              service_cost: $('#recommended-service-price').text(),
              estimated_commission: $('#commission').text()
            },
            context: $(this),
            success: function(response, status, jqXHR) {
                data[1] = response.number_printers_serviced;
                data[2] = response.total_mono_pages;
                data[3] = response.total_color_pages;
                data[4] = response.base_volume_mono || '---';
                data[5] = +response.base_rate_mono ? response.base_rate_mono : '---';
                data[6] = response.base_volume_color || '---';
                data[7] = +response.base_rate_color ? response.base_rate_color : '---';
                data[8] = +response.rcmd_cpp_mono ? Number.parseFloat(response.rcmd_cpp_mono).toFixed(4) : '---';
                data[9] = +response.rcmd_cpp_color ? Number.parseFloat(response.rcmd_cpp_color).toFixed(4) : '---';

                row.data(data).draw();

                location.reload(); // TODO Refreshing for now; recalculate tier and summary values without reload later
            },
        });
    } else {
        let short_model = $('#networkDevice-shortName :selected').text();

        let proposed_network_service = {
            printer: parseInt($('#networkDevice-shortName').val()),
            number_printers_serviced: parseInt($('#networkDevice-quantity').val()),
            total_mono_pages: parseInt($('#total-monthly-mono-pages').val()) || 0,
            total_color_pages: parseInt($('#total-monthly-color-pages').val()) || 0,
            mono_coverage: $('#mono-coverage').val(),
            color_coverage: $('#color-coverage').val(),
            mono_toner_price: $('#rcmdp-mono-toner').text().replace(/\$/g, '').replace('---', 0),
            color_toner_price: $('#rcmdp-color-toner').text().replace(/\$/g, '').replace('---', 0),
            base_volume_mono: parseInt($('#base-volume-mono').val()) || 0,
            base_volume_color: parseInt($('#base-volume-color').val()) || 0,
            base_rate_mono: isNaN(parseFloat($('#base-rate-mono').val())) ? 0 : parseFloat($('#base-rate-mono').val()).toFixed(2),
            base_rate_color: isNaN(parseFloat($('#base-rate-color').val())) ? 0 :parseFloat($('#base-rate-color').val()).toFixed(2),
            rcmd_cpp_mono: proposal_settings.proposal_type !== 'ppc' ? $('#rcmdp-mono-sales').text().replace(/\$/g, '').replace('---', 0) || 0 : isNaN(parseFloat($('#proposed-mono-sales').val())) ? 0 : parseFloat($('#proposed-mono-sales').val()).toFixed(4),
            rcmd_cpp_color: proposal_settings.proposal_type !== 'ppc' ? $('#rcmdp-color-sales').text().replace(/\$/g, '').replace('---', 0) || 0 : isNaN(parseFloat($('#proposed-mono-sales').val())) ? 0 : parseFloat($('#proposed-mono-sales').val()).toFixed(4),
            proposed_cpp_mono: isNaN(parseFloat($('#proposed-mono-sales').val())) ? 0 : parseFloat($('#proposed-mono-sales').val()).toFixed(4),
            proposed_cpp_color: isNaN(parseFloat($('#proposed-color-sales').val())) ? 0 : parseFloat($('#proposed-color-sales').val()).toFixed(4),
            calculated_cpp_mono: $('#raw-mono-cpp').text().substring(1),
            calculated_cpp_color: $('#raw-color-cpp').text().substring(1),
            service_cost: $('#rcmdp-service').text().replace(/\$/g, '').replace('---', 0),
            estimated_commission: isNaN(parseFloat($('#commission').text().replace(/\$/g, ''))) ? 0 : parseFloat($('#commission').text().replace(/\$/g, '')).toFixed(2),
            is_non_network: false
        };

        let buy_or_lease = '';
        let lease_type = '';
        let proposed_cost = 0;
        let estimated_commission = 0;

        let proposed_network_device = {};
        if (saveEquipment) {
            buy_or_lease = $('#buy-lease').val();
            proposed_cost = $('#equipment-purchase-price').val();
            estimated_commission = $('#eqcommission').html();
            

            var lease_term = 0;
            var lease_buyout = 0;
            // save lease_type (gel 04-29-2020)
            var lease_payment = 0;
            if (buy_or_lease === 'lease') {
                lease_term = $('#lease-term option:selected').text();
                lease_type = $('#lease-type option:selected').text();
                lease_payment = $('#monthly-payment').val();
                lease_buyout = $('#leaseBuyout').val();
            }

            // allow rentals (gel 05-15-2020)
            if (buy_or_lease === 'rent') {
                lease_term = $('#rent-term option:selected').text();
                lease_type = $('#rent-type option:selected').text();
                lease_payment = $('#rent-monthly-payment').val();
                lease_buyout = $('#rentBuyout').val();
            }

            proposed_network_device = {
                buy_or_lease: buy_or_lease,
                proposed_cost: proposed_cost,
                number_printers_purchased: $('#networkDevice-quantity').val(),
                duty_cycle: 0,
                long_model: $('#device-dropdown1 option:selected').text(),
                out_cost: $('#total-outcost').val(),
                msrp_cost: $('#total-msrpcost').val(),
                care_pack_cost: 0,
                estimated_commission: estimated_commission,
                lease_payment: lease_payment,
                lease_buyout: lease_buyout,
                lease_term: lease_term,
                lease_type: lease_type
            
            };
            //proposal_purchase_items.push(proposed_network_device);
            saveEquipment = false;
        }

        $.ajax({
            type: 'POST',
            cache: false,
            data: {
                proposed_service: JSON.stringify(proposed_network_service),
                proposed_purchase: JSON.stringify(proposed_network_device)
            },
            url: window.location.origin + '/proposal/addNetworkDevice/' + proposal_id + '/'
        }).done(function (response) {
            let id = JSON.parse(response).service_item_id;
            proposed_network_service['short_model'] = short_model;
            proposed_network_service['is_color_device'] = printer_details.printer_is_color_type;
            proposed_network_service['id'] = id;
            proposed_network_service['buy_or_lease'] = buy_or_lease;
            proposed_network_service['proposed_cost'] = proposed_cost;

            let purchase_item_id = JSON.parse(response).purchase_item_id;
            if (purchase_item_id) {
                proposed_network_device['id'] = purchase_item_id;
                proposal_purchase_items.push(proposed_network_device);
            }

            $.ajax({
                type: 'GET',
                cache: false,
                url: window.location.origin + '/proposal/getUpdatedProposalServiceItems/' + proposal_id + '/'
            }).done(function (response) {
                proposal_service_items = response;
                updatePObjects();
                appendToTierTable(id);
                if(proposal_settings.proposal_type !== 'ppc') {
                    appendToNetworkTable(proposed_network_service, purchase_item_id);  
                } else {
                    appendToNetworkTable(proposal_service_items.filter(obj => {
                        return obj.id === id
                    })[0], purchase_item_id);
                }
                
                appendToCartridgeTable(proposal_service_items.filter(obj => {
                        return obj.id === id
                    })[0]
                );
                appendFlatRaceTable(proposal_service_items.filter(obj => {
                        return obj.id === id
                    })[0]
                );
                $('#addNetworkDevice').foundation('close');
                updateSummaryAndMonthly();
            });

        }).fail(function () {
            alert('failed to add network device');
        });
    }

});

$('#nonNetworkDevice-shortName').on('change', function () {
    getNonNetDeviceDetails($(this).children('option:selected').text(), $(this).children('option:selected').val(), $('#non-network-mono-coverage').val(), $('#non-network-color-coverage').val());
    $('#add-non-network-device').removeAttr('disabled');
});

$('#nonNetworkDevice-quantity').on('change', function () {
    updateNonNetTotalPrice($('#nonNetworkDevice-price').val());
    updateNonNetDeviceComission(non_network_details.non_network_commission);
});

// implement Staples request to lock margins   (gel 2019-11-25)
// needed to prevent changes to total pages because it is used to equalize margin.
$("#lock-margin").attr('title', 'Auto-adjust proposed color/mono sales price to maintain margin.');
$('#lock-margin').on('change', function () {
    if($('#lock-margin').val() == '1') {
        $('#total-monthly-mono-pages').attr('disabled', true);
        $('#total-monthly-color-pages').attr('disabled', true);                
    } else {
        $('#total-monthly-mono-pages').attr('disabled', false);
        $('#total-monthly-color-pages').attr('disabled', false);  
    }   
});

// make base rates recalculate if volumes are adjusted  (gel 2019-12-03)
$('#base-volume-mono').on('change keyup', function () {
    $('#base-rate-mono').val(($('#base-volume-mono').val() * $('#proposed-mono-sales').val()).toFixed(2));
});

$('#base-volume-color').on('change keyup', function () {
    $('#base-rate-color').val(($('#base-volume-color').val() * $('#proposed-color-sales').val()).toFixed(2));
});

// implement Staples request to lock margins   (gel 2019-11-25)
// handle changes to mono based on typed input.
$('#proposed-mono-sales').on('change keyup', function () {
    if($('#lock-margin').val() == '1') {
        let changeType = "mono";
        equalizeMargin(changeType);             
    } else {
        $('#base-rate-mono').val(($('#base-volume-mono').val() * $('#proposed-mono-sales').val()).toFixed(2));
        $('#saved-mono-sales').val($('#proposed-mono-sales').val());
    }
});

// handle changes to color based on typed input.
$('#proposed-color-sales').on('change keyup', function () {
    if($('#lock-margin').val() == '1') {
        let changeType = "color";
        equalizeMargin(changeType);             
    } else {
        $('#base-rate-color').val(($('#base-volume-color').val() * $('#proposed-color-sales').val()).toFixed(2));
        $('#saved-color-sales').val($('#proposed-color-sales').val());
    }
});

$('#non-network-mono-coverage').on('change', function () {
    getNonNetDeviceDetails($('#nonNetworkDevice-shortName :selected').text(), $('#nonNetworkDevice-shortName :selected').val(), $(this).val(), $('#non-network-color-coverage').val());
});

$('#non-network-color-coverage').on('change', function () {
    getNonNetDeviceDetails($('#nonNetworkDevice-shortName :selected').text(), $('#nonNetworkDevice-shortName :selected').val(), $('#non-network-mono-coverage').val(), $(this).val());
});

$('#add-non-network-device').on('click', function () {
    let short_model = $('#nonNetworkDevice-shortName :selected').text();
    let proposed_non_network_service = {
        printer: parseInt($('#nonNetworkDevice-shortName').val()),
        number_printers_serviced: parseInt($('#nonNetworkDevice-quantity').val()),
        non_network_cost: $('#nonNetworkDevice-price').val(),
        mono_coverage: $('#non-network-mono-coverage').val(),
        color_coverage: $('#non-network-color-coverage').val(),
        estimated_commission: $('#nonNetwork-commission').text().replace(/\$/g, ''),
        is_non_network: true
    };

    $.ajax({
        type: 'POST',
        cache: false,
        data: {
            proposed_service: JSON.stringify(proposed_non_network_service),
            proposed_purchase: JSON.stringify({})
        },
        url: window.location.origin + '/proposal/addNetworkDevice/' + proposal_id + '/'
    }).done(function (response) {
        let id = JSON.parse(response).service_item_id;
        proposed_non_network_service['short_model'] = short_model;
        proposed_non_network_service['is_color_device'] = non_network_details.printer_is_color_type;
        proposed_non_network_service['id'] = id;

        $.ajax({
            type: 'GET',
            cache: false,
            url: window.location.origin + '/proposal/getUpdatedProposalServiceItems/' + proposal_id + '/'
        }).done(function (response) {
            proposal_service_items = response;
            appendToNonNetworkTable(proposed_non_network_service);
            appendToCartridgeTable(proposal_service_items.filter(obj => {
                    return obj.id === id
                })[0]
            );

            $('#addNonNetworkDevice').foundation('close');

            p_objects[id] = {
                service: proposed_non_network_service,
                equipment: {},
                mono_tier: null,
                color_tier: null
            };

            updateSummaryAndMonthly();
        });

    }).fail(function () {
        alert('failed to add non-network device');
    });

});

$('#equipment-options-close').on('click', function() {
    clearEquipmentOptionsValues();
});

function clearEquipmentOptionsValues() {
    let zero = '0.00';
    $('#device-dropdown1').val(-1);
    $('#deviceOutcost1').val(zero);
    $('#deviceMsrp1').val(zero);
    $('#total-outcost').val(zero);
    $('#total-msrpcost').val(zero);
    $('#equipment-purchase-price').val(zero);
    $('#margin').val(zero);
    $('#margin-percentage').val(zero);
    $('.accessory-row').remove();
    $('#addAccessory1').prop('disabled', true);
//    $('#monthly-payment').val(0);
    $('#buy-lease').val('buy');
    $('#lock-margin').val(0);
//  disable modal buttons until sub-model is selected
    $('#save-new-network-device').prop('disabled', true);
    $('#open-lease-options').prop('disabled', true);
    $('#open-rent-options').prop('disabled', true);
//  reset equipment cost in cpp info
    $('#changePurchaseOption').val('0')
    $('#priceInCPPSection').addClass('hide');
    $('#price-in-cpp-mono').val('0.00');
    $('#price-in-cpp-color').val('0.00');
    $('#price-in-color').addClass('hide');
}

function updateSummaryAndMonthly() {
    updateSummaryInfo();
    calculateMargin();
    updateMonthlyTotals();
    updateOverallMargin();
}

function appendToNetworkTable(newDevice, purchase_item_id) {
    network_devices.push(newDevice);
    
    let monoCPP = proposal_settings.proposal_type !== 'ppc' ? newDevice.proposed_cpp_mono == 0 ? newDevice.rcmd_cpp_mono : newDevice.proposed_cpp_mono : newDevice.recommended_cost_per_cartridge_mono;
    monoCPP = monoCPP == null ? 0 : monoCPP;
    monoCPP = monoCPP === 0 ? '-' : monoCPP;
    let colorCPP = proposal_settings.proposal_type !== 'ppc' ? newDevice.proposed_cpp_color == 0 ? newDevice.rcmd_cpp_color : newDevice.proposed_cpp_color : newDevice.recommended_cost_per_cartridge_color;
    colorCPP = colorCPP == null ? 0 : colorCPP;
    colorCPP = colorCPP === 0 ? '-' : colorCPP;

    // Update UI with buy/lease and price for purchased/leased equipment (GEL 2019-11-20)
    let purchaseDevice;
    let buy_or_lease = '-';
    let proposed_cost = '0.00';
    // todo optimize the following code... 
    if (purchase_item_id === "") {
        purchase_item_id = null;
    };
    if (purchase_item_id != null) {
        purchaseDevice = loadProposalPurchaseItem(purchase_item_id);
        buy_or_lease = purchaseDevice.buy_or_lease;
        proposed_cost = addThousandsSeparator(parseFloat(purchaseDevice.proposed_cost).toFixed(2));
    } else if (newDevice.proposal_purchase_item_id != null) {
        purchaseDevice = loadProposalPurchaseItem(newDevice.proposal_purchase_item_id);
        buy_or_lease = purchaseDevice.buy_or_lease;
        proposed_cost = addThousandsSeparator(parseFloat(purchaseDevice.proposed_cost).toFixed(2)); 
    } else {
        buy_or_lease = '-';
        proposed_cost = '0.00';
    };

    let currentRow = network_table.row.add(
        [
            newDevice.short_model,
            addThousandsSeparator(newDevice.number_printers_serviced == 0 ? '---' : newDevice.number_printers_serviced),
            addThousandsSeparator(newDevice.total_mono_pages == 0 ? '---' : newDevice.total_mono_pages),
            addThousandsSeparator(newDevice.total_color_pages == 0 ? '---' : newDevice.total_color_pages),
            addThousandsSeparator(newDevice.base_volume_mono == 0 ? '---' : newDevice.base_volume_mono),
            newDevice.base_rate_mono == 0 ? '---' : ('$' + addThousandsSeparator(parseFloat(newDevice.base_rate_mono).toFixed(2))),
            addThousandsSeparator(newDevice.base_volume_color == 0 ? '---' : newDevice.base_volume_color),
            newDevice.base_rate_color == 0 ? '---' : ('$' + addThousandsSeparator(parseFloat(newDevice.base_rate_color).toFixed(2))),
            addThousandsSeparator(monoCPP),
            addThousandsSeparator(colorCPP),
            buy_or_lease,
            proposed_cost,
            '<button data-type="remove-device"><i class="fas fa-times-circle size-21 red-delete-icon"></i></button>'
        ]
    ).draw().node();

    $(currentRow).attr('data-id', newDevice.id);
    $(currentRow).dblclick(function () {
        loadNetworkDeviceModal(newDevice.id);

        if(proposal_service_items.length >1) {
            loadTransferPagesModal(newDevice.id);
            $('#transferButton').removeClass('hide');
        } else {
            $('#transferButton').addClass('hide');
        };

        $('#addNetworkDevice').foundation('open');
        // loadNetworkItem(newDevice);
    });
}

// Get the values from purchased (buy/lease) items on the proposal (GEL 2019-11-20)
function loadProposalPurchaseItem(proposal_purchase_item_id) {
    var return_data;
    $.ajax({
        type: 'GET',
        async: false,
        cache: false,
        url: window.location.origin + '/proposal/getProposalPurchaseItem/' + proposal_purchase_item_id
    }).done(function (response) {
        return_data = JSON.parse(response);
    }).fail(function (error) {
        console.logalert(error);
    });
    return return_data;
}

function appendToNonNetworkTable(proposed_non_network_device) {
    non_network_devices.push(proposed_non_network_device);
    let currentRow = non_network_table.row.add(
        [proposed_non_network_device.short_model,
            addThousandsSeparator(proposed_non_network_device.number_printers_serviced == 0 ? '---' : proposed_non_network_device.number_printers_serviced),
            addThousandsSeparator(proposed_non_network_device.non_network_cost == 0 ? '---' : proposed_non_network_device.non_network_cost),
            '<button data-type="remove-device"><i class="fas fa-times-circle size-21 red-delete-icon"></i></button>',]
    ).draw().node();

    $(currentRow).attr('data-id', proposed_non_network_device.id);
    $(currentRow).dblclick(function () {
        $('#addNonNetworkDevice').foundation('open');
        loadNonNetworkItem(proposed_non_network_device);
    });
}

// Populates list of manufacturers in a selection box
function loadMakeDetails() {
    $.ajax({
        type: 'GET',
        cache: false,
        url: window.location.origin + '/proposal/getMakeDetails/'
    }).done(function (response) {
        let makes = JSON.parse(response).makes;
        appendMakeDetails($('#networkDevice-makeName'), makes);
        appendMakeDetails($('#nonNetworkDevice-makeName'), makes);
    }).fail(function (error) {
        console.log(error);
    });
}

function appendMakeDetails(makeDropDown, makes) {
    makeDropDown.append($('<option>', { value: -1, text: '', hidden: true }));
    for (let i = 0; i < makes.length; i++) {
        let make = makes[i];
        makeDropDown.append($('<option>', { value: make[0], text: make[1] }));
    }
}
// Reinitialize the non-network device dropdown (GEL)
function loadPrinterDetailsByMakeNN() {
    // Clear the shortName dropdown so selected make devices can be appended.
    $('#nonNetworkDevice-shortName').children().remove().end();

    $.ajax({
        type: 'GET',
        cache: false,
        url: window.location.origin + '/proposal/getPrinterDetailsByMake/' + $("#nonNetworkDevice-makeName :selected").val()
    }).done(function (response) {
        let printers = JSON.parse(response).printers;
        appendPrinterDetailsByMake($('#nonNetworkDevice-shortName'), printers);
    }).fail(function (error) {
        console.log(error);
    });
}

// insert function to retrieve Proposal settings (GEL 2019-12-04)
function loadProposalSettings(proposal_id) {
    var return_data;
    $.ajax({
        type: 'GET',
        async: false,
        cache: false,
        url: window.location.origin + '/proposal/getProposalSettings/' + proposal_id
    }).done(function (response) {
        return_data = JSON.parse(response);
    }).fail(function (error) {
        alert(error);
    });
    return return_data;
}

// Reinitialize the device dropdown
function loadPrinterDetailsByMake() {
    // Clear the shortName dropdown so selected make devices can be appended.
    $('#networkDevice-shortName').children().remove().end();

    $.ajax({
        type: 'GET',
        cache: false,
        url: window.location.origin + '/proposal/getPrinterDetailsByMake/' + $("#networkDevice-makeName :selected").val()
    }).done(function (response) {
        let printers = JSON.parse(response).printers;
        appendPrinterDetailsByMake($('#networkDevice-shortName'), printers);
    }).fail(function (error) {
        console.log(error);
    });
}

function appendPrinterDetailsByMake(deviceDropDown, printers) {
    deviceDropDown.append($('<option>', { value: -1, text: '', hidden: true }));
    for (let i = 0; i < printers.length; i++) {
        let printer = printers[i];
        deviceDropDown.append($('<option>', { value: printer[0], text: printer[1] }));
    }
}

function loadPrinterDetails() {
    $.ajax({
        type: 'GET',
        cache: false,
        url: window.location.origin + '/proposal/getPrinterDetails/'
    }).done(function (response) {
        let printers = JSON.parse(response).printers;
        appendPrinterDetails($('#networkDevice-shortName'), printers);
        appendPrinterDetails($('#nonNetworkDevice-shortName'), printers);
    }).fail(function (error) {
        console.log(error);
    });
}

function appendPrinterDetails(deviceDropDown, printers) {
    deviceDropDown.append($('<option>', { value: -1, text: '', hidden: true }));
    for (let i = 0; i < printers.length; i++) {
        let printer = printers[i];
        deviceDropDown.append($('<option>', { value: printer[0], text: printer[1] }));
    }
}

$('#mono-coverage').change(() => {
    setMonoCPP();
});

$('#color-coverage').change(() => {
    setColorCPP();
});

function getNetDeviceDetails(deviceId) {
    $.ajax({
        type: 'POST',
        cache: false,
        data: { 'device_id': deviceId, 'proposal_id': proposal_id },
        url: window.location.origin + '/proposal/getNetworkDeviceDetails/'
    }).done(function (response) {
        printer_costs = response.printer_costs;
        printer_details = response.printer_details;
        toner_costs = response.toners_costs;
        accessories = response.accessories;
        page_cost_details = response.page_cost_details;

        const monoCoverage = $('#mono-coverage').val();
        const colorCoverage = $('#color-coverage').val();
        // pageInfo.monoCoverage = monoCoverage;
        // pageInfo.colorCoverage = colorCoverage;

        // const finalMonoCpp = toner_costs.mono_cpp * (monoCoverage / 0.05);
        // const finalColorCpp = toner_costs.color_cpp * (colorCoverage / 0.05);
        // console.log('getting');
        // $('#raw-mono-cpp').text(`$${(finalMonoCpp + '').substring(0,6)}`);
        // $('#raw-color-cpp').text(`$${(finalColorCpp + '').substring(0,6)}`);
        setMonoCPP();
        setColorCPP();
        if (toner_costs.warning) {
            alert('No available toner for this printer model. Check with your manager.');
        }

        // Allow pricing display to toggle on/off per Harry (GEL 2019-08-27)
        var show_pricing = false;
        if (show_pricing == true) {
            $('#show-pricing').removeClass('hide');
        }
        // Default in average monthly volumes for mono and color (GEL 2019-08-31)
        // Update base volume mono   (GEL 2019-11-20)
        // Implement the auto-populate volume and rate calculation (GEL 2019-12-05)
        if(modal_mode == 'new') {
            $('#total-monthly-mono-pages').val(printer_details.avm_mono);
            $('#def-monthly-mono-pages').val(printer_details.avm_mono);
            $('#def-monthly-color-pages').val(0);
            $('#retail-mono-price').html(printer_details.retail_mono);
            // $('#retail-total-sales-mono-price').html(printer_details.retail_mono);
            $('#bundled-monthly-mono-pages').val(printer_details.avm_mono);
            $('#rent-bundled-monthly-mono-pages').val(printer_details.avm_mono);
            if ( $('#base-volume-mono').val() ) {
                
            } else {
                if (proposal_settings.auto_pop_base) {
                    $('#base-volume-mono').val(page_cost_details.def_base_volume_mono);
                } else {
                    $('#base-volume-mono').val(0);
                    $('#base-rate-mono').val(0);
                }    
            } 
            $('#proposed-mono-sales').val('');
            $('#proposed-color-sales').val('');
        }

        if (printer_details.printer_is_color_type == true) {
            $('#lock-margin-option').removeClass('hide');
            $('#total-monthly-color-pages').parent().parent().removeClass('hide');
            $('#included-monthly-color-pages').parent().parent().removeClass('hide');
            $('#included-color-section').removeClass('hide');
            $('#bundled-monthly-color-pages').parent().parent().removeClass('hide');
            $('#bundled-color-section').removeClass('hide');
            $('#rent-bundled-monthly-color-pages').parent().parent().removeClass('hide');
            $('#rent-bundled-color-section').removeClass('hide');
            $('#color-coverage').parent().parent().parent().removeClass('hide');
            $('#rcmdp-color-toner').parent().removeClass('hide');
            $('#rcmdp-color-sales').parent().removeClass('hide');
            $('#raw-color-cpp2').parent().removeClass('hide');
            $('#base-volume-color').parent().parent().removeClass('hide');
            $('#base-rate-color').parent().parent().parent().removeClass('hide');
            $('#proposed-color-sales').parent().parent().parent().removeClass('hide');
            $('#lock-margin').attr('disabled', false);
            if($('#lock-margin').val() == '1') {
                $('#total-monthly-mono-pages').attr('disabled', true);
                $('#total-monthly-color-pages').attr('disabled', true);                
            } else {
                $('#total-monthly-mono-pages').attr('disabled', false);
                $('#total-monthly-color-pages').attr('disabled', false);   
            }
            if(modal_mode == 'new') {
                $('#total-monthly-color-pages').val(printer_details.avm_color);
                $('#def-monthly-color-pages').val(printer_details.avm_color);
                $('#retail-color-price').html(printer_details.retail_color);
                // $('#retail-total-sales-color-price').html(printer_details.retail_color);
                // add conditional when autopopbase is false set to zero
                if (proposal_settings.auto_pop_base) {
                    $('#base-volume-color').val(page_cost_details.def_base_volume_color);
                } else {
                    $('#base-volume-color').val(0);
                    $('#base-rate-color').val(0);
                }
            }
            $('#color-coverage').attr('disabled', false);
            $('#base-volume-color').attr('disabled', false);
            $('#base-rate-color').attr('disabled', false);
            $('#proposed-color-sales').attr('disabled', false);
        } else {
            // update the hidden values for the calculation
            $('#total-monthly-color-pages').val(0);
            $('#included-monthly-color-pages').val(0);
            $('#included-color-monthly').val(0);
            $('#bundled-monthly-color-pages').val(0);
            $('#rent-bundled-monthly-color-pages').val(0);
            $('#base-volume-color').val(0);
            $('#base-rate-color').val(0);
            $('#proposed-color-sales').val(0);
            // remove all color related rows
            $('#lock-margin-option').addClass('hide');
            $('#total-monthly-color-pages').parent().parent().addClass('hide');
            $('#included-color-section').addClass('hide');
            $('#bundled-monthly-color-pages').parent().parent().addClass('hide');
            $('#bundled-color-section').addClass('hide');
            $('#rent-bundled-monthly-color-pages').parent().parent().addClass('hide');
            $('#rent-bundled-color-section').addClass('hide');
            $('#color-coverage').parent().parent().parent().addClass('hide');
            $('#rcmdp-color-toner').parent().addClass('hide');
            $('#rcmdp-color-sales').parent().addClass('hide');
            $('#raw-color-cpp2').parent().addClass('hide');
            $('#base-volume-color').parent().parent().addClass('hide');
            $('#base-rate-color').parent().parent().parent().addClass('hide');
            $('#proposed-color-sales').parent().parent().parent().addClass('hide');
            $('#lock-margin').attr('disabled', true);
            if($('#lock-margin').val() == '1') {
                $('#total-monthly-mono-pages').attr('disabled', true);              
            } else {
                $('#total-monthly-mono-pages').attr('disabled', false);  
            }
            $('#total-monthly-color-pages').attr('disabled', true);
            $('#color-coverage').attr('disabled', true);
            $('#base-volume-color').attr('disabled', true);
            $('#base-rate-color').attr('disabled', true);
            $('#proposed-color-sales').attr('disabled', true);
        }

        setDeviceSelectOptions($('#device-dropdown1'), printer_costs);
        $('#total-monthly-mono-pages').trigger('input');
        // Moved this line up one to fix a timing issue... not sure why it worked (gel 2020-05-07)
        //setDeviceSelectOptions($('#device-dropdown1'), printer_costs);
    }).fail(function (xhr, status, e) {
        alert(xhr + ' ' + status + ' ' + e);
    });
}

function loadNetworkItem(item) {

}

function selectPurchaseDevice(dropdown, rowNum) {
    let device = printer_costs[$(dropdown).val()];
    let quantity = parseInt($('#networkDevice-quantity').val());
    let outCost = parseFloat(device.outCost) * (1 + mgmtAsmpts.equipment_inflate) * quantity;
    let msrp = parseFloat(device.msrp) * quantity;
    $('#deviceOutcost' + rowNum).val(outCost.toFixed(2));
    $('#deviceMsrp' + rowNum).val(msrp.toFixed(2));

    if ($(dropdown).val() != -1) {
        $('#save-new-network-device').prop('disabled', false);
        $('#open-lease-options').prop('disabled', false);
        $('#open-rent-options').prop('disabled', false);
    } else {
        $('#save-new-network-device').prop('disabled', true);
        $('#open-lease-options').prop('disabled', true);
        $('#open-rent-options').prop('disabled', true);
    }
    updateDeviceTotalCosts(rowNum);

    if (!jQuery.isEmptyObject(accessories)) {
        $('#addAccessory' + rowNum).prop('disabled', false);
    }

    // where is leaseDeviceName in the html? commented code out (gel 05-15-2020)
    //$('#leaseDeviceName').html(dropdown.options[dropdown.selectedIndex].innerHTML);
}


function setDeviceSelectOptions(dropdown, printer_costs) {
    dropdown.empty();
    dropdown.append($('<option>', { value: -1, text: 'Select Device', selected: true, hidden: true }));
    for (let printer_cost in printer_costs) {
        dropdown.append($('<option>', { value: printer_costs[printer_cost].id, text: printer_costs[printer_cost].model_name }));
    }
}

function updateDeviceTotalCosts(rowNum) {
    let dOut = parseFloat($('#deviceOutcost' + rowNum).val());
    let dMsrp = parseFloat($('#deviceMsrp' + rowNum).val());
    let accOut = 0.0;
    let accMsrp = 0.0;

    $.each($('[data-device-section=' + rowNum + ']').find('[data-item-type=acc]'), function (index, accCost) {
        let price = parseFloat($(accCost).val());
        if($(accCost).data('price-type') === 'out') {
            accOut += price;
        } else {
            accMsrp += price;
        }
    });
    $('#total-outcost').val((dOut + accOut).toFixed(2));
    $('#total-msrpcost').val((dMsrp + accMsrp).toFixed(2));
    // where is leaseDevicePrice in the html? commented code out (gel 05-15-2020)
    //$('#leaseDevicePrice').val($('#total-outcost').val());
    $('#equipment-purchase-price').val(($('#total-outcost').val() / (1 - mgmtAsmpts.target_margin_equipment)).toFixed(2));
    updateOverallMargin();
}

// changed = to == in the if statement to address Firefox error message  (GEL 12-16-2019)
function updateBundledLease() {
    if ($('#leaseSelectionType option:selected').text() == "Straight Lease") {
        $('#bundledSection').show();
    } else {
        $('#bundledSection').hide();
    };
    getLeasingData();
}

function updateBundledRent() {
    if ($('#rentSelectionType option:selected').text() == "Straight Rental") {
        $('#rentbundledSection').show();
    } else {
        $('#rentbundledSection').hide();
    };
    getRentalData();
}

function updateMargin() {
    $('#equipment-purchase-price').val(($('#margin').val()*1 +$('#total-outcost').val()*1).toFixed(2));
    if($('#leaseBuyout').val()===""){
        $('#leaseBuyout').val(0);
    }
    if($('#rentBuyout').val()===""){
        $('#rentBuyout').val(0);
    }
    if($('#equipment-purchase-price').val()===""){
        $('#equipment-purchase-price').val(0);
    }
    $('#leasePurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#leaseBuyout').val());
    $('#rentPurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#rentBuyout').val());
    $('#margin-percentage').val(($('#margin').val() / $('#equipment-purchase-price').val() * 100).toFixed(2));
    updateEquipmentCommissions();
}

function updatePercent() {
    $('#equipment-purchase-price').val(($('#total-outcost').val() / (1 - ($('#margin-percentage').val()/100))).toFixed(2));
    if($('#leaseBuyout').val()===""){
        $('#leaseBuyout').val(0);
    }
    if($('#rentBuyout').val()===""){
        $('#rentBuyout').val(0);
    }
    if($('#equipment-purchase-price').val()===""){
        $('#equipment-purchase-price').val(0);
    }
    $('#leasePurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#leaseBuyout').val());
    $('#rentPurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#rentBuyout').val());
    $('#margin').val(($('#equipment-purchase-price').val() - $('#total-outcost').val()).toFixed(2));
    updateEquipmentCommissions();
}

//  insert feature request by Staples to auto adjust to maintain recommened margin.   (GEL 2019-11-25)
function equalizeMargin(changeType) {
    let rm_price = parseFloat($('#rcmdp-mono-sales').text().replace(/\$/g, '').replace('---', 0) || 0);
    let rc_price = parseFloat($('#rcmdp-color-sales').text().replace(/\$/g, '').replace('---', 0) || 0);
    let tm_pages = $('#total-monthly-mono-pages').val()*1;
    let tc_pages = $('#total-monthly-color-pages').val()*1;

    let base_total = (rm_price * tm_pages) + (rc_price * tc_pages);

    let pm_price = parseFloat($('#proposed-mono-sales').val());
    let pc_price = parseFloat($('#proposed-color-sales').val());

    let sm_price = parseFloat($('#saved-mono-sales').text().replace(/\$/g, '').replace('---', 0) || pm_price);
    let sc_price = parseFloat($('#saved-color-sales').text().replace(/\$/g, '').replace('---', 0) || pc_price);


    if ($('#proposed-mono-sales').val() == $('#saved-mono-sales').val()) {
        changeType = 'color';
    } else {
        changeType = 'mono';
    }

    if (changeType == 'mono') {
        $('#proposed-color-sales').val(((base_total - (pm_price * tm_pages))/tc_pages).toFixed(4));
    } else {
        $('#proposed-mono-sales').val(((base_total - (pc_price * tc_pages))/tm_pages).toFixed(4));
    }

    $('#base-rate-mono').val(($('#base-volume-mono').val() * $('#proposed-mono-sales').val()).toFixed(2));
    $('#base-rate-color').val(($('#base-volume-color').val() * $('#proposed-color-sales').val()).toFixed(2));

    $('#saved-mono-sales').val($('#proposed-mono-sales').val());
    $('#saved-color-sales').val($('#proposed-color-sales').val());
}

function updateOverallMargin() {
    $('#margin').val(($('#equipment-purchase-price').val() - $('#total-outcost').val()).toFixed(2));
    $('#margin-percentage').val(($('#margin').val() / $('#equipment-purchase-price').val() * 100).toFixed(2));
    if($('#leaseBuyout').val()===""){
        $('#leaseBuyout').val(0);
    }    
    if($('#rentBuyout').val()===""){
        $('#rentBuyout').val(0);
    }   
    if($('#equipment-purchase-price').val()===""){
        $('#equipment-purchase-price').val(0);
    }
    $('#leasePurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#leaseBuyout').val());
    $('#rentPurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#rentBuyout').val());
    updateEquipmentCommissions();
}

function updateEquipmentCommissions(deviceType) {
    let NetEquipmentCommission = 0;

    switch (mgmtAsmpts.eq_commission_type) {
        case 'eq_flat_margin':
            NetEquipmentCommission = mgmtAsmpts.eq_percent_margin_flat_rate * $('#margin').val();
            $('#eqcommission').html(`${NetEquipmentCommission.toFixed(2)}`);
            break;
        case 'eq_flat_revenue':
            NetEquipmentCommission = mgmtAsmpts.eq_percentage_revenue_flat_rate * $('#equipment-purchase-price').val();
            $('#eqcommission').html(`${NetEquipmentCommission.toFixed(2)}`);
            break;
        case 'eq_blended_margin':
            NetEquipmentCommission = (deviceType == 'printer' ? mgmtAsmpts.eq_margin_rate_printers : mgmtAsmpts.eq_margin_rate_copiers) * $('#margin').val();
            $('#eqcommission').html(`${NetEquipmentCommission.toFixed(2)}`);
            break;
        case 'eq_blended_revenue':
            NetEquipmentCommission = (deviceType == 'printer' ? mgmtAsmpts.eq_revenue_rate_printers : mgmtAsmpts.eq_revenue_rate_copiers) * $('#equipment-purchase-price').val();
            $('#eqcommission').html(`${NetEquipmentCommission.toFixed(2)}`);
            break;
        default:
    
    }
}

function updateMonthlyPages(monoPages, colorPages) {
    $('#total-monthly-pages').val(monoPages + colorPages);
    return monoPages + colorPages;
}

function updateMonoCPP(scaledTonerCPP, scaledServiceCPP, monoCoverage) {
    let monoCPP = getMonoCPP(scaledTonerCPP, scaledServiceCPP, monoCoverage);

    $('#raw-mono-cpp').val(monoCPP);

    return monoCPP;
}

function getMonoCPP(scaledTonerCPP, scaledServiceCPP, monoCoverage) {
    if (mgmtAsmpts.contract_service_type === 'service_only') {
        return +((scaledTonerCPP) * (monoCoverage / 0.05)).toFixed(4);
    } else if (mgmtAsmpts.contract_service_type === 'supplies_only'){
        return +((scaledTonerServiceCPP) * (monoCoverage / 0.05)).toFixed(4);
    } else {
        return +((scaledTonerCPP + scaledServiceCPP) * (monoCoverage / 0.05)).toFixed(4); 
    }
}

function updateRecommendMonoTonerPrice(scaledTonerCPP, pages, monoCoverage) {
    // service only = 0
    if (mgmtAsmpts.contract_service_type === 'service_only') {
        $('#recommended-mono-toner-price').html('0');
        return 0;
    }

    let monoTonerPrice = getRecommendMonoTonerPrice(scaledTonerCPP, pages, monoCoverage);

    // supplies only bump (GEL 2020-04-07)
    if (mgmtAsmpts.contract_service_type === 'supplies_only') {
        monoTonerPrice = parseFloat(monoTonerPrice * (1 + mgmtAsmpts.supplies_only)).toFixed(4);
    };

    $('#recommended-mono-toner-price').html(monoTonerPrice);
    return monoTonerPrice;
}

function getRecommendMonoTonerPrice(scaledTonerCPP, pages, monoCoverage) {
    // Pages * (CPP * Coverage / 0.05) / (1 - Toner Margin)
    return +(pages * (scaledTonerCPP * (monoCoverage / 0.05))).toFixed(4); // return float instead of string
}

function updateRecommendColorTonerPrice(colorTonerMarginPrice, totalMonthlyColorPages, colorCoverage) {
    // if service only, return 0
    if (mgmtAsmpts.contract_service_type === 'service_only') {
        $('#recommended-color-toner-price').html('0');
        return 0;
    }

    let colorTonerPrice = getRecommendColorTonerPrice(colorTonerMarginPrice, totalMonthlyColorPages, colorCoverage);

    // supplies only bump (GEL 2020-04-07)
    if (mgmtAsmpts.contract_service_type === 'supplies_only') {
        colorTonerPrice = (colorTonerPrice * (1 + mgmtAsmpts.supplies_only)).toFixed(4);
    }

    $('#recommended-color-toner-price').html(colorTonerPrice);
    return colorTonerPrice;
}

function getRecommendColorTonerPrice(colorTonerMarginPrice, totalMonthlyColorPages, colorCoverage) {
    return +(colorTonerMarginPrice * totalMonthlyColorPages * colorCoverage / 0.05).toFixed(4);
    // return float instead of string
}

function updateRecommendServicePrice(serviceBumpedMarginPrice, totalMonthlyPages) {
    // supply only = 0
    if (mgmtAsmpts.contract_service_type === 'supplies_only' || serviceBumpedMarginPrice === 0 || totalMonthlyPages === 0) {
        $('#recommended-service-price').html('0');
        return 0;
    }

    let servicePrice = getRecommendServicePrice(serviceBumpedMarginPrice, totalMonthlyPages);
    $('#recommended-service-price').html(servicePrice);
    return servicePrice;
}

function getRecommendServicePrice(serviceBumpedMarginPrice, totalMonthlyPages) {
    return +(serviceBumpedMarginPrice * totalMonthlyPages).toFixed(4); // return float instead of string
}

function updateRecommendMonthlyPrice(monoTonerPrice, colorTonerPrice, servicePrice) {
    let monthlyPrice = parseFloat(monoTonerPrice + colorTonerPrice + servicePrice).toFixed(4);
    if (+monthlyPrice === 0) {
        $('#recommended-monthly-price').html('0');
        return 0;
    }

    $('#recommended-monthly-price').html(monthlyPrice);
    return +monthlyPrice;       // return float instead of string
}

function updateRecommendMonoSalesPrice(monoTonerPrice, servicePrice, monoPages, colorPages) {
    if (monoPages === 0) {
        $('#recommended-mono-sales-price').html('0.0000');
        $('#recommended-mono-sales-price2').val(0);
        $('#included-mono-price').val(0);
        $('#bundled-mono-price').val(0);
        $('#rent-recommended-mono-sales-price').html('0.0000');
        $('#rent-recommended-mono-sales-price2').val(0);
        $('#rent-bundled-mono-price').val(0);
        return 0;
    }

    let monoSalesPrice = getRecommendMonoSalesPrice(monoTonerPrice, servicePrice, monoPages, colorPages);
    $('#recommended-mono-sales-price').html(monoSalesPrice);
    $('#recommended-mono-sales-price2').val(monoSalesPrice);
    $('#rent-recommended-mono-sales-price2').val(monoSalesPrice);
    if ( !$.trim($('#proposed-mono-sales').val())) {
        $('#proposed-mono-sales').val(monoSalesPrice);
    }

    // if not ppc go ahead and update the modal with cpp price.
    
    if(proposal_settings.proposal_type !== 'ppc') {
        let selfServiceMonoPrice = getSelfServiceMonoPrice(monoTonerPrice, servicePrice, monoPages, colorPages);
        $('#self-service-mono-price').html(selfServiceMonoPrice);
    }
    

    // pre-calculate base rate  (gel 2019-11-25)
    if ( !$.trim($('#base-rate-mono').val())) {
        $('#base-rate-mono').val(($('#proposed-mono-sales').val() * page_cost_details.def_base_volume_mono).toFixed(2));
    }

    $('#included-mono-price').val(monoSalesPrice);
    $('#bundled-mono-price').val(monoSalesPrice);
    $('#rent-bundled-mono-price').val(monoSalesPrice);
    return monoSalesPrice;
}

function getRecommendMonoSalesPrice(monoTonerPrice, servicePrice, monoPages, colorPages) {
    return +((monoTonerPrice + (servicePrice * monoPages / (monoPages + colorPages))) / monoPages).toFixed(4);
    // return float instead of string
}

function getSelfServiceMonoPrice(monoTonerPrice, servicePrice, monoPages, colorPages) {
    return +((monoTonerPrice + (servicePrice * monoPages / (monoPages + colorPages))) / monoPages).toFixed(4); 
}

/**
 * Update modal to show the PPC pricing it's proposal type (ppc).
 */
async function getSelfServicePPCMonoPrice() {
        const device_id = $('#networkDevice-shortName').val();
        const self_service_api_url = '/api/self-service-ppc/' + proposal_id + '/' + device_id + '/';

        const ppc_calc = await fetch(self_service_api_url)
        .then(res => res.json())
        .catch(error => console.error(error));

        console.log('printer details: ',printer_details);
        const selfServiceMonoPrice = ppc_calc.ppc_mono;
        $('#self-service-mono-price').html(selfServiceMonoPrice);

        const retail_price = printer_details.retail_mono;
        const total_savings = retail_price !== 0 ? (Math.abs(retail_price - selfServiceMonoPrice)).toFixed(2) : 0;
        $('#retail-total-sales-mono-price').html(total_savings);

        return selfServiceMonoPrice;
}

// function updateSelfServiceMonoPrice(monoTonerPrice, servicePrice, monoPages, colorPages) {
//     // if (monoPages === 0) {
//     //     $('#self-service-mono-price').html('0.00');
//     // }

//     let selfServiceMonoPrice = getSelfServiceMonoPrice(monoTonerPrice, servicePrice, monoPages, colorPages);
//     $('#self-service-mono-price').html(selfServiceMonoPrice);
//     console.log(selfServiceMonoPrice);


//     return selfServiceMonoPrice;
// }

/**
 * Update modal to show the PPC pricing it's proposal type (ppc).
 */
async function getSelfServicePPCColorPrice() {
        const device_id = $('#networkDevice-shortName').val();
        const self_service_api_url = '/api/self-service-ppc/' + proposal_id + '/' + device_id + '/';

        const ppc_calc = await fetch(self_service_api_url)
        .then(res => res.json())
        .catch(error => console.error(error));
    
        const selfServiceColorPrice = ppc_calc.ppc_color;
        $('#self-service-color-price').html(selfServiceColorPrice);

        const retail_price = printer_details.retail_color;
        const total_savings = retail_price !== 0 ? (Math.abs(retail_price - selfServiceColorPrice)).toFixed(2) : 0;

        $('#retail-total-sales-color-price').html(total_savings);
        return selfServiceColorPrice;
}

function getSelfServiceColorPrice(colorTonerPrice, servicePrice, monoPages, colorPages) {
    return +((colorTonerPrice + (servicePrice * colorPages / (monoPages + colorPages))) / colorPages).toFixed(4); 
}

function updateRecommendColorSalesPrice(colorTonerPrice, servicePrice, monoPages, colorPages) {
    if (colorPages === 0) {
        $('#recommended-color-sales-price').html('0.0000');
        $('#raw-color-cpp').html('0.0000');
        $('#recommended-color-sales-price2').val(0);
        $('#included-color-price').val(0);
        $('#bundled-color-price').val(0);
        return 0;
    }

    let colorSalesPrice = getRecommendColorSalesPrice(colorTonerPrice, servicePrice, monoPages, colorPages);
    $('#recommended-color-sales-price').html(colorSalesPrice);
    $('#recommended-color-sales-price2').val(colorSalesPrice);
    $('#rent-recommended-color-sales-price2').val(colorSalesPrice);
    if ( !$.trim($('#proposed-color-sales').val())) {
        $('#proposed-color-sales').val(colorSalesPrice);
    }

    // pre-calculate base rate  (gel 2019-11-25)
    if ( !$.trim($('#base-rate-color').val())) {
        $('#base-rate-color').val(($('#proposed-color-sales').val() * page_cost_details.def_base_volume_color).toFixed(2));
    }

    // if not ppc the update modal to show color pricing.
    if(proposal_settings.proposal_type !== 'ppc') {
        let selfServiceColorPrice = getSelfServiceColorPrice(colorTonerPrice, servicePrice, monoPages, colorPages);
        $('#self-service-color-price').html(selfServiceColorPrice);
    }

    $('#included-color-price').val(colorSalesPrice);
    $('#bundled-color-price').val(colorSalesPrice);
    $('#rent-bundled-color-price').val(colorSalesPrice);
    
    return colorSalesPrice 
}

function getRecommendColorSalesPrice(colorTonerPrice, servicePrice, monoPages, colorPages) {
    return +((colorTonerPrice + (servicePrice * colorPages / (monoPages + colorPages))) / colorPages).toFixed(4);
    // return float instead of string
}

function resetNetworkDeviceModal() {
    // reset the modal UI to the default/initial state
    $('#networkDevice-shortName').val('');
    $('#networkDevice-shortName').prop('disabled', false);
    $('#networkDevice-quantity').val('1');
    $('#equipment-options').prop('disabled', true);
    // reset include purchase in cpp options
    $('#changePurchaseOption').val('0')
    $('#priceInCPPSection').addClass('hide');
    $('#open-lease-options').prop('disabled', false);
    $('#open-rent-options').prop('disabled', false);
    $('#price-in-cpp-mono').val('0.00');
    $('#price-in-cpp-color').val('0.00');
    $('#price-in-color').addClass('hide');
    // transfer pages (GEL 02/10/2020)
    $('#transferButton').addClass('hide');
    $('#sourceMonoPages').val('');
    $('#sourceMonoPages').prop('disabled', true);
    $('#networkDevice-totalOutcost').val('');
    $('#networkDevice-totalOutcost').prop('disabled', true);
    $('#networkDevice-purchasePrice').val('');
    $('#networkDevice-purchasePrice').prop('disabled', true);
    $('#total-monthly-mono-pages').val('');
    $('#total-monthly-color-pages').val('');
    $('#total-monthly-pages').val('');
    $('#mono-coverage').val('.05');
    $('#color-coverage').val('.05');
    $('#color-coverage').prop('disabled', true);
    $('#recommended-mono-toner-price').html('0');
    $('#recommended-color-toner-price').html('0');
    $('#recommended-service-price').html('0');
    $('#recommended-monthly-price').html('0');
    $('#recommended-mono-sales-price').html('0.0000');
    $('#recommended-color-sales-price').html('0.0000');
    $('#self-service-mono-price').val('0.00');
    $('#self-service-color-price').val('0.00');
    $('#retail-mono-price').val('0.00');
    $('#retail-color-price').val('0.00');
    $('#raw-mono-cpp').val('0.0000');
    $('#raw-color-cpp').val('0.0000');
    // lease section
    $('#included-monthly-mono-pages').val('');
    $('#included-monthly-color-pages').val('');
    $('#included-mono-price').val(0);
    $('#included-color-price').val(0);
    $('#included-mono-monthly').val(0);
    $('#included-color-monthly').val(0);
    $('#includedAmt').val(0);
    $('#bundled-monthly-mono-pages').val(0);
    $('#bundled-monthly-color-pages').val(0);
    $('#recommended-mono-sales-price2').val(0);
    $('#recommended-color-sales-price2').val(0);
    $('#bundled-mono-price').val(0);
    $('#bundled-color-price').val(0);
    $('#bundled-mono-monthly').val(0);
    $('#bundled-color-monthly').val(0);
    $('#bundledAmt').val(0);
    // rent section
    $('#rent-bundled-monthly-mono-pages').val(0);
    $('#rent-bundled-monthly-color-pages').val(0);
    $('#rent-recommended-mono-sales-price2').val(0);
    $('#rent-recommended-color-sales-price2').val(0);
    $('#rent-bundled-mono-price').val(0);
    $('#rent-bundled-color-price').val(0);
    $('#rent-bundled-mono-monthly').val(0);
    $('#rent-bundled-color-monthly').val(0);
    $('#rent-bundledAmt').val(0);
    // end lease-rent sections
    $('#base-volume-mono').val('');
    $('#base-volume-color').val('');
    $('#base-volume-color').prop('disabled', true);
    $('#base-rate-mono').val('');
    $('#base-rate-color').val('');
    $('#base-rate-color').prop('disabled', true);
    $('#proposed-mono-sales').val('');
    $('#proposed-color-sales').val('');
    $('#commission').html('0.00');
    $('#add-network-device').prop('disabled', true);
    $('#add-network-device').data('id', null);
    $('#add-network-device').html('Add');
//    $('#monthly-payment').val(0);
    $('#buy-lease').val('buy');
}

function loadNetworkDeviceModal(id) {
    modal_mode = 'edit';
    const p = p_objects[id];

    $('#networkDevice-shortName').val(p.service.printer_id);
    $('#networkDevice-shortName').trigger('change');
    $('#networkDevice-shortName').prop('disabled', true);

    $('#networkDevice-quantity').val(p.service.number_printers_serviced);

    // leasing stuff
    // TODO not sure how lease/buy stuff works, ask Harry
    // $('#equipment-options').prop('disabled', true); TODO figure out what leased items look like
    // $('#networkDevice-totalOutcost').val('');
    // $('#networkDevice-totalOutcost').prop('disabled', true);
    // $('#networkDevice-purchasePrice').val('');
    // $('#networkDevice-purchasePrice').prop('disabled', true);

    $('#total-monthly-mono-pages').val(p.service.total_mono_pages);
    $('#bundled-monthly-mono-pages').val(p.service.total_mono_pages);
    $('#rent-bundled-monthly-mono-pages').val(p.service.total_mono_pages);
    $('#mono-coverage').val(p.service.mono_coverage.toFixed(2).replace('0.', '.'));

    // add conditional when autopopbase is false set to zero
    if (proposal_settings.auto_pop_base) {
        $('#base-volume-mono').val(page_cost_details.def_base_volume_mono);
    } else {
        $('#base-volume-mono').val(0);
    }
    $('#base-volume-mono').val(p.service.base_volume_mono);
    $('#base-rate-mono').val(p.service.base_rate_mono);
    $('#proposed-mono-sales').html(p.service.proposed_cpp_mono);

    if (p.service.is_color_device) {
        $('#total-monthly-color-pages').val(p.service.total_color_pages);
        $('#bundled-monthly-color-pages').val(0);
        $('#rent-bundled-monthly-color-pages').val(0);
        $('#color-coverage').val(p.service.color_coverage.toFixed(2).replace('0.', '.'));
        // add conditional when autopopbase is false set to zero (GEL 2019-12-05)
        if (proposal_settings.auto_pop_base) {
            $('#base-volume-color').val(page_cost_details.def_base_volume_color);
        } else {
            $('#base-volume-color').val(0);
        }
        $('#base-volume-color').val(p.service.base_volume_color);
        $('#base-rate-color').val(p.service.base_rate_color);
        $('#proposed-color-sales').html(p.service.proposed_cpp_color);
    }

    $('#add-network-device').prop('disabled', false);
    $('#add-network-device').html('Save');
    $('#add-network-device').data('id', p.service.id);
    $('#total-monthly-mono-pages').trigger('input');

}

function loadTransferPagesModal(id) {
    //modal_mode = 'edit';
    const p = p_objects[id];
    // PrinterServiceItem.id is stored in "id"

    // Initialize the source device fields
    $('#sourceDevice-shortName').val($('#networkDevice-shortName :selected').text());
    $('#sourceMonoPages').val(p.service.total_mono_pages);
    if (p.service.is_color_device) {
        $('#sourceColorPages').val(p.service.total_color_pages);
    } else {
        $('#sourceColorPages').val('0');
    };

    // Initialize the destination device fields (exclude the source device) unless
    // the selected device previously had pages transferred - then use them instead.
    $('#destination-dropdown1').children().remove().end();
    $('#destinationMonoPages').val('0');
    $('#destinationColorPages').val('0');
    $('#fromID').val(id);

    if (p.service.transfer_id == undefined || p.service.transfer_id == null) {
        appendServiceItemDetails($('#destination-dropdown1'), id);
        $('#toID').val('0');
        $('#destination-dropdown1').prop('disabled', false);
        $('#transferMonoPages').val('0');
        $('#transferMonoPages').prop('disabled', true);
        $('#priorMonoPages').val('0');
        $('#transferColorPages').val('0');
        $('#transferColorPages').prop('disabled', true);
        $('#priorColorPages').val('0');
    } else {
        setDefaultServiceItem($('#destination-dropdown1'), p.service.transfer_id);
        $('#toID').val(p.service.transfer_id);
        $('#destination-dropdown1').prop('disabled', true);
        $('#transferMonoPages').val(-1*p.service.transfer_mono_pages);
        $('#priorMonoPages').val(-1*p.service.transfer_mono_pages);
        $('#transferMonoPages').prop('disabled', false);
        $('#transferColorPages').val(-1*p.service.transfer_color_pages);
        $('#priorColorPages').val(-1*p.service.transfer_color_pages); 
        let color_transfer = Number($('#transferColorPages').val()) + Number($('#destinationColorPages').val());
        if (p.service.is_color_device && color_transfer > 0) {
            $('#transferColorPages').prop('disabled', false);
        } else {
            $('#transferColorPages').prop('disabled', true);
        };
    };
    
    // Hide the working variables stored in HTML
    $('#fromID').addClass('hide');
    $('#toID').addClass('hide');
    $('#priorMonoPages').addClass('hide');
    $('#priorColorPages').addClass('hide');

} 

function appendServiceItemDetails(dropdown, id) {
    dropdown.append($('<option>', { value: -1, text: '', hidden: true }));
    let device_count = 0;

    for (let i = 0; i < proposal_service_items.length; i++) {
        let item = proposal_service_items[i];
        if (item.id == id || item.transfer_id > 0) {
            continue;
        } else {
            dropdown.append($('<option>', { value: item.id, text: item.short_model }));
            device_count += 1;
        };
    };
    
    // If empty, let user know "why" drop-down is blank.
    if (device_count == 0) {
        $('#destination-dropdown1').attr('title', 'None available. All other devices already involved in a transfer.');
    } else {
        $('#destination-dropdown1').attr('title', '');        
    }
}

function setDefaultServiceItem(dropdown, id) {
    for (let i = 0; i < proposal_service_items.length; i++) {
        let item = proposal_service_items[i];
        if (item.id == id) {
            dropdown.append($('<option>', { value: item.id, text: item.short_model }));
            $('#toID').val(item.id);
            $('#destinationMonoPages').val(item.total_mono_pages);
            if (item.is_color_device) {
                $('#destinationColorPages').val(item.total_color_pages);
            } else {
                $('#destinationColorPages').val('0');
            };
        } else {
            continue;
        };
    };
}

function selectDestinationDevice(dropdown, rowNum) {
    for (let i = 0; i < proposal_service_items.length; i++) {
        let item = proposal_service_items[i];
        if (item.id == $(dropdown).val()) {
            $('#toID').val(item.id);
            $('#destinationMonoPages').val(item.total_mono_pages);
            if (item.is_color_device) {
                $('#destinationColorPages').val(item.total_color_pages);
            } else {
                $('#destinationColorPages').val('0');
            };
            continue;
        };
    };

    // Undo any changes from a prior select (if any).  This allows user to select a device,
    // transfer pages and then change their mind.  Selecting a new destination device will 
    // revert any transferred pages so they can start fresh with the new destination device.
    var sMono = Number($('#sourceMonoPages').val()) + Number($('#transferMonoPages').val());
    var sColor = Number($('#sourceColorPages').val()) + Number($('#transferColorPages').val());
    $('#sourceMonoPages').val(sMono);
    $('#sourceColorPages').val(sColor);

    // Clear any prior transfer values
    $('#transferMonoPages').val('0');
    $('#priorMonoPages').val('0');
    $('#transferColorPages').val('0');
    $('#priorColorPages').val('0');

    // Make transfer fields available depending on device types 
    $('#transferMonoPages').prop('disabled', false);
    if( $('#sourceColorPages').val() != '0' && $('#destinationColorPages').val() != '0') {
        $('#transferColorPages').prop('disabled', false);
    } else {
        $('#transferColorPages').prop('disabled', true);
    };

}

$('#transferMonoPages').on('keyup change', function () {
    // priorMonoPages stores the prior value of transferMonoPages
    var tMono = Number($('#transferMonoPages').val());
    var sMono = Number($('#sourceMonoPages').val()) + Number($('#priorMonoPages').val());
    var dMono = Number($('#destinationMonoPages').val()) - Number($('#priorMonoPages').val());

    // Do not let sourceMonoPages go negative
    if (sMono < tMono) {
        //alert('tMono reset to sMono');
        tMono = sMono;
    };
    
    // Adjust the working values
    sMono -= tMono;
    dMono += tMono;

    // Update the UI
    $('#sourceMonoPages').val(sMono);
    $('#destinationMonoPages').val(dMono);
    $('#transferMonoPages').val(tMono);
    $('#priorMonoPages').val(tMono);
    
});

$('#transferColorPages').on('keyup change', function () {
    // priorColorPages stores the prior value of transferColorPages
    var tColor = Number($('#transferColorPages').val());
    var sColor = Number($('#sourceColorPages').val()) + Number($('#priorColorPages').val());
    var dColor = Number($('#destinationColorPages').val()) - Number($('#priorColorPages').val());

    // Do not let sourceColorPages go negative
    if (sColor < tColor) {
        tColor = sColor;
    };
    
    // Adjust the working values
    sColor -= tColor;
    dColor += tColor;

    // Update the UI
    $('#sourceColorPages').val(sColor);
    $('#destinationColorPages').val(dColor);
    $('#transferColorPages').val(tColor);
    $('#priorColorPages').val(tColor);
    
});

$('#transfer-update').on('click', function () {
    // Update the UI values on the Add/Edit Network Device source reveal
    $('#total-monthly-mono-pages').val($('#sourceMonoPages').val());
    $('#total-monthly-color-pages').val($('#sourceColorPages').val());

    // Update the destination ProposalServiceItem in the DB ()
    // If the transfer pages are zero the transfer-id will be clearing in model_update
    for (let i = 0; i < proposal_service_items.length; i++) {
        let item = proposal_service_items[i];
        if (item.id == Number($('#toID').val())) {
            item.total_mono_pages = Number($('#destinationMonoPages').val());
            item.total_color_pages = Number($('#destinationColorPages').val());
            item.transfer_id = Number($('#fromID').val());
            item.transfer_mono_pages = Number($('#transferMonoPages').val());
            item.transfer_color_pages = Number($('#transferColorPages').val());
        } else if (item.id == Number($('#fromID').val())) {
            item.total_mono_pages = Number($('#sourceMonoPages').val());
            item.total_color_pages = Number($('#sourceColorPages').val());
            item.transfer_id = Number($('#toID').val());
            item.transfer_mono_pages = -1 * Number($('#transferMonoPages').val());
            item.transfer_color_pages = -1 * Number($('#transferColorPages').val());
        } 
    };

    // Update the p values for both source & destination
    const p = p_objects[Number($('#fromID').val())];
    const q = p_objects[Number($('#toID').val())]; 
    
    // Update the dsource ProposalServiceItem
    $.ajax({
        type: 'POST',
        cache: false,
        data: {
            'proposalServiceItem_data': JSON.stringify(p.service)
        },
        url: window.location.origin + '/proposal/updateProposalServiceItem/',
        error: function (xhr, status, e) {
            alert('function error');
            alert(xhr + ' ' + status + ' ' + e);
        }
    }).done (function(response) {
        //window.location.href = '/repDashboard';      
    });    
   
    // Update the destination ProposalServiceItem
    $.ajax({
        type: 'POST',
        cache: false,
        data: {
            'proposalServiceItem_data': JSON.stringify(q.service)
        },
        url: window.location.origin + '/proposal/updateProposalServiceItem/',
        error: function (xhr, status, e) {
            alert('function error');
            alert(xhr + ' ' + status + ' ' + e);
        }
    }).done (function(response) {
        //window.location.href = '/repDashboard';       
    });    
    
}); 

/**
 * Calculate the commission based on management assumptions.
 *
 * This is different than what's in the previous version of the function;
 * it's based on a formula sent by Harry.
 */
function updateNetDeviceCommission(deviceType, pageInfo, recommendedPrice, proposedPrice) {
    let NetDeviceCommission = 0;
    let price = recommendedPrice.monthly;
    let cost = recommendedPrice.monthly * (1-((mgmtAsmpts.target_margin_toner + mgmtAsmpts.target_margin_service)/2));

    if ( Object.values(proposedPrice).some(each => Boolean(each)) ) {
        const base = proposedPrice.baseMonoRate + proposedPrice.baseColorRate;
        const mono = proposedPrice.monoSalesPrice * (pageInfo.monoMonthly - proposedPrice.baseMonoVolume);
        const color = proposedPrice.colorSalesPrice * (pageInfo.colorMonthly - proposedPrice.baseColorVolume);

        price = base + mono + color;

    }

    switch (mgmtAsmpts.commission_type) {
        case 'flat_margin':
            NetDeviceCommission = mgmtAsmpts.percent_margin_flat_rate * (price - cost);
            $('#commission').html(`${NetDeviceCommission.toFixed(2)}`);
            break;
        case 'flat_revenue':
            NetDeviceCommission = mgmtAsmpts.percentage_revenue_flat_rate * price;
            $('#commission').html(`${NetDeviceCommission.toFixed(2)}`);
            break;
        case 'blended_margin':
            NetDeviceCommission = (deviceType == 'printer' ? mgmtAsmpts.margin_rate_printers : mgmtAsmpts.margin_rate_copiers) * (price - cost);
            $('#commission').html(`${NetDeviceCommission.toFixed(2)}`);
            break;
        case 'blended_revenue':
            NetDeviceCommission = (deviceType == 'printer' ? mgmtAsmpts.revenue_rate_printers : mgmtAsmpts.revenue_rate_copiers) * price;
            $('#commission').html(`${NetDeviceCommission.toFixed(2)}`);
            break;
        default:

    }
}

function getNonNetDeviceDetails(printerModel, device_Id, monoCoverage, colorCoverage) {
    $.ajax({
        type: 'POST',
        cache: false,
        data: { 'network_device_short_name': printerModel, 'device_id': device_Id, 'proposal_id': proposal_id, 'mono_coverage': monoCoverage, 'color_coverage': colorCoverage },
        url: window.location.origin + '/proposal/getNonNetworkDeviceDetails/'
    }).done(function (response) {
        non_network_details = response.non_network_details;

        if (non_network_details.warning) {
            alert('No available toner for this printer model. Check with your manager.');
        }
        // Show message if lookup for PageCost failed otherwise unlock ADD button (GEL)
        if (response.non_network_unit_price ==0) {
            $('#add-non-network-device').attr('disabled', true);
            alert('No available toner for this printer model. Check with your manager or try another model')
        } else {
            $('#add-non-network-device').attr('disabled', false);
        }

        $('#nonNetworkDevice-price').val(parseFloat(response.non_network_unit_price).toFixed(2));
        updateNonNetTotalPrice(parseFloat(response.non_network_unit_price));
        updateNonNetDeviceComission(non_network_details.non_network_commission);
        if (non_network_details.printer_is_color_type == true) {
            $('#non-network-color-coverage').parent().parent().parent().removeClass('hide');
            $('#non-network-color-coverage').attr('disabled', false);
        } else {
            // remove all color related rows
            $('#non-network-color-coverage').parent().parent().parent().addClass('hide');
            $('#non-network-color-coverage').attr('disabled', true);
        }
    }).fail(function (xhr, status, e) {
        alert(xhr + ' ' + status + ' ' + e);
    });
}

function loadNonNetworkItem(item) {
    $('#nonNetwork-commission').text('$ ' + item.estimated_commission);
}

function updateNonNetTotalPrice(unitPrice) {
    $('#nonNetworkDevice-total-price').val(($('#nonNetworkDevice-quantity').val() * unitPrice).toFixed(2));
}

function updateNonNetDeviceComission(unitCommission) {
    let nonNetworkDeviceQuantity = $('#nonNetworkDevice-quantity').val();
    $('#nonNetwork-commission').text('$ ' + (unitCommission * nonNetworkDeviceQuantity).toFixed(2));
}

function resetRunningTotals() {
    runningMonoPrice = 0;
    runningMonoColorPrice = 0;
    runningColorPrice = 0;
    runningMonoCost = 0;
    runningColorCost = 0;
    runningMonoColorCost = 0;
}

function updateSummaryInfo() {
    $('.term').text(mgmtAsmpts.term);

    resetRunningTotals();

    let baseVolMono = 0;
    let baseVolMonoColor = 0;
    let baseVolColor = 0;
    let baseRateMono = 0;
    let baseRateMonoColor = 0;
    let baseRateColor = 0;
    let overMono = 0;
    let overMonoColor = 0;
    let overColor = 0;

    for (let i of Object.keys(p_objects)) {
        let device = p_objects[i].service;
        // only include network devices
        if (device.is_non_network) continue;

        let serviceCost = parseFloat(device.service_cost) * (1 - mgmtAsmpts.target_margin_service);
        let totalPages = device.total_mono_pages + device.total_color_pages;

        let rcmdMonoToner;
        let rcmdColorToner;
        let sf_mono_price;
        let sf_color_price;
        $.ajax({
            type: 'POST',
            cache: false,
            data: { 'device_id': device.printer_id, 'proposal_id': device.proposal_id },
            url: window.location.origin + '/proposal/getNetworkDeviceDetails/',
            async: false
        }).done(function (response) {
            toner_costs = response.toners_costs;
            rcmdMonoToner = getRecommendMonoTonerPrice(toner_costs.scaled_mono_cost, device.total_mono_pages, device.mono_coverage);
            rcmdColorToner = getRecommendColorTonerPrice(toner_costs.scaled_color_cost, device.total_color_pages, device.color_coverage);
            let rcmdService = getRecommendServicePrice(toner_costs.scaled_service_cost, totalPages);

            sf_mono_price = getRecommendMonoSalesPrice(rcmdMonoToner, rcmdService, device.total_mono_pages, device.total_color_pages);
            sf_color_price = getRecommendColorSalesPrice(rcmdColorToner, rcmdService, device.total_mono_pages, device.total_color_pages);
        });

        if (device.is_color_device) {
            //================= monocolor
            baseVolMonoColor += device.base_volume_mono;
            baseRateMonoColor += parseFloat(device.base_rate_mono);

            let overage = device.total_mono_pages - device.base_volume_mono;
            overMonoColor += overage > 0 ? overage : 0;

            let salesPrice;

            salesPrice = parseFloat(device.proposed_cpp_mono) > 0 ? parseFloat(device.proposed_cpp_mono) : parseFloat(device.rcmd_cpp_mono);
            runningMonoColorPrice += salesPrice * overage + parseFloat(device.base_rate_mono);

            let monoColorCost = parseFloat(device.mono_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
            runningMonoColorCost += totalPages === 0 ? 0 : monoColorCost + (serviceCost * device.total_mono_pages / totalPages);

            //================= color
            baseVolColor += device.base_volume_color;
            baseRateColor += parseFloat(device.base_rate_color);

            overage = device.total_color_pages - device.base_volume_color;
            overColor += overage > 0 ? overage : 0;

            if (streetFighter && sf_color_price) {
                device.rcmd_cpp_color = sf_color_price;
                device.color_toner_price = rcmdColorToner;
                let serviceItem = proposal_service_items.find(x => x.id === device.id);
                serviceItem.rcmd_cpp_color = sf_color_price;
                let row = network_table.row('[data-id="'+ device.id +'"]');
                row.cell('td:nth-of-type(10)').data(sf_color_price).draw()
            }
            salesPrice = parseFloat(device.proposed_cpp_color) > 0 ? parseFloat(device.proposed_cpp_color) : parseFloat(device.rcmd_cpp_color);
            runningColorPrice += salesPrice * overage + parseFloat(device.base_rate_color);

            let colorCost = parseFloat(device.color_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
            runningColorCost += totalPages === 0 ? 0 : colorCost + (serviceCost * device.total_color_pages / totalPages);
        } else {
            //================= mono
            baseVolMono += device.base_volume_mono;
            baseRateMono += parseFloat(device.base_rate_mono);
            let overage = device.total_mono_pages - device.base_volume_mono;
            overMono += overage > 0 ? overage : 0;
            let salesPrice;
            if (streetFighter && sf_mono_price) {
                device.rcmd_cpp_mono = sf_mono_price;
                device.mono_toner_price = rcmdMonoToner;
                let serviceItem = proposal_service_items.find(x => x.id === device.id);
                serviceItem.rcmd_cpp_mono = sf_mono_price;
                let row = network_table.row('[data-id="'+ device.id +'"]');
                row.cell('td:nth-of-type(9)').data(sf_mono_price).draw()
            }
            salesPrice = parseFloat(device.proposed_cpp_mono) > 0 ? parseFloat(device.proposed_cpp_mono) : parseFloat(device.rcmd_cpp_mono);
            runningMonoPrice += salesPrice * overage + parseFloat(device.base_rate_mono);
            let monoCost = parseFloat(device.mono_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
            runningMonoCost += totalPages === 0 ? 0 : monoCost + (serviceCost * device.total_mono_pages / totalPages);
        }
    }
    $('#total-mono-base-volume').text(addThousandsSeparator(baseVolMono));
    $('#total-mono-base-rate').text('$' + addThousandsSeparator(baseRateMono.toFixed(2)));
    $('#overage-mono-volume').text(addThousandsSeparator(overMono));
    $('#monoBlended').text(overMono != 0 ? '$' + ((runningMonoPrice - baseRateMono) / overMono).toFixed(4) : '$0');
    monoMargin = runningMonoPrice > 0 ? ((runningMonoPrice - runningMonoCost) / runningMonoPrice * 100).toFixed(0) : 0;
    $('#monoMargin').text(monoMargin + '%');
    if (monoMargin / 100 < mgmtAsmpts.min_mono_margin) {
        $('#monoMargin').addClass('warning');
    } else {
        $('#monoMargin').removeClass('warning');
    }

    $('#total-mono-on-color-base-volume').text(addThousandsSeparator(baseVolMonoColor));
    $('#total-mono-on-color-base-rate').text('$' + addThousandsSeparator(baseRateMonoColor.toFixed(2)));
    $('#overage-mono-on-color-volume').text(addThousandsSeparator(overMonoColor));
    $('#monoColorBlended').text(overMonoColor != 0 ? '$' + ((runningMonoColorPrice - baseRateMonoColor) / overMonoColor).toFixed(4) : '$0');
    monoColorMargin = runningMonoColorPrice > 0 ? ((runningMonoColorPrice - runningMonoColorCost) / runningMonoColorPrice * 100).toFixed(0) : 0;
    $('#monoColorMargin').text(monoColorMargin + '%');
    if (monoColorMargin / 100 < mgmtAsmpts.min_mono_on_color_margin) {
        $('#monoColorMargin').addClass('warning');
    } else {
        $('#monoColorMargin').removeClass('warning');
    }

    $('#total-color-base-volume').text(addThousandsSeparator(baseVolColor));
    $('#total-color-base-rate').text('$' + addThousandsSeparator(baseRateColor.toFixed(2)));
    $('#overage-color-volume').text(addThousandsSeparator(overColor));
    $('#colorBlended').text(overColor != 0 ? '$' + ((runningColorPrice - baseRateColor) / overColor).toFixed(4) : '$0');
    colorMargin = runningColorPrice > 0 ? ((runningColorPrice - runningColorCost) / runningColorPrice * 100).toFixed(0) : 0;
    $('#colorMargin').text(colorMargin + '%');
    if (colorMargin / 100 < mgmtAsmpts.min_color_margin) {
        $('#colorMargin').addClass('warning');
    } else {
        $('#colorMargin').removeClass('warning');
    }
}

// eslint-disable-next-line no-unused-vars
function calculateMargin() {
    let runningMonoColorPriceLocal = 0;
    let runningMonoColorCostLocal = 0;
    let runningColorPriceLocal = 0;
    let runningColorCostLocal = 0;
    let runningMonoPriceLocal = 0;
    let runningMonoCostLocal = 0;
    for (let i of Object.keys(p_objects)) {
        let device = p_objects[i].service;
        // only include network devices
        if (device.is_non_network) continue;

        let serviceCost = parseFloat(device.service_cost) * (1 - mgmtAsmpts.target_margin_service);
        let totalPages = device.total_mono_pages + device.total_color_pages;
        if (device.is_color_device) {
            //================= monocolor
            let overage = device.total_mono_pages - device.base_volume_mono;

            let salesPrice = 0;
            if (!isNullOrWhitespace($('#monoColorCPP').val())) {
                salesPrice = parseFloat($('#monoColorCPP').val());
            } else {
                salesPrice = parseFloat(device.proposed_cpp_mono) > 0 ? parseFloat(device.proposed_cpp_mono) : parseFloat(device.rcmd_cpp_mono);
            }

            runningMonoColorPriceLocal += salesPrice * overage + parseFloat(device.base_rate_mono);

            let monoColorCost = parseFloat(device.mono_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
            runningMonoColorCostLocal += totalPages === 0 ? 0 : monoColorCost + (serviceCost * device.total_mono_pages / totalPages);

            //================= color
            overage = device.total_color_pages - device.base_volume_color;

            if (!isNullOrWhitespace($('#colorCPP').val())) {
                salesPrice = parseFloat($('#colorCPP').val());
            } else {
                salesPrice = parseFloat(device.proposed_cpp_color) > 0 ? parseFloat(device.proposed_cpp_color) : parseFloat(device.rcmd_cpp_color);
            }
            runningColorPriceLocal += salesPrice * overage + parseFloat(device.base_rate_color);

            let colorCost = parseFloat(device.color_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
            runningColorCostLocal += totalPages === 0 ? 0 : colorCost + (serviceCost * device.total_color_pages / totalPages);
        } else {
            //================= mono
            let overage = device.total_mono_pages - device.base_volume_mono;

            let salesPrice = 0;
            if (!isNullOrWhitespace($('#monoCPP').val())) {
                salesPrice = parseFloat($('#monoCPP').val());
            } else {
                salesPrice = parseFloat(device.proposed_cpp_mono) > 0 ? parseFloat(device.proposed_cpp_mono) : parseFloat(device.rcmd_cpp_mono);
            }
            runningMonoPriceLocal += salesPrice * overage + parseFloat(device.base_rate_mono);
            let monoCost = parseFloat(device.mono_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
            runningMonoCostLocal += totalPages === 0 ? 0 : monoCost + (serviceCost * device.total_mono_pages / totalPages);
        }
    }

    monoMargin = runningMonoPriceLocal > 0 ? ((runningMonoPriceLocal - runningMonoCostLocal) / runningMonoPriceLocal * 100).toFixed(0) : 0;
    $('#monoMargin').text(monoMargin + '%');
    if (monoMargin / 100 < mgmtAsmpts.min_mono_margin) {
        $('#monoMargin').addClass('warning');
    } else {
        $('#monoMargin').removeClass('warning');
    }
    monoColorMargin = runningMonoColorPriceLocal > 0 ? ((runningMonoColorPriceLocal - runningMonoColorCostLocal) / runningMonoColorPriceLocal * 100).toFixed(0) : 0;
    $('#monoColorMargin').text(monoColorMargin + '%');
    if (monoColorMargin / 100 < mgmtAsmpts.min_mono_on_color_margin) {
        $('#monoColorMargin').addClass('warning');
    } else {
        $('#monoColorMargin').removeClass('warning');
    }
    colorMargin = runningColorPriceLocal > 0 ? ((runningColorPriceLocal - runningColorCostLocal) / runningColorPriceLocal * 100).toFixed(0) : 0;
    $('#colorMargin').text(colorMargin + '%');
    if (colorMargin / 100 < mgmtAsmpts.min_color_margin) {
        $('#colorMargin').addClass('warning');
    } else {
        $('#colorMargin').removeClass('warning');
    }
}

function updateMonthlyTotals() {
    let netPriceTotal = runningColorPrice + runningMonoPrice + runningMonoColorPrice;
    $('#monthlyNetPrice').text('$' + addThousandsSeparator(netPriceTotal.toFixed(2)));
    $('#monthlyNetPrice').attr('val', addThousandsSeparator(netPriceTotal.toFixed(2)));

    let netCostTotal = runningColorCost + runningMonoCost + runningMonoColorCost;
    let netMargin = netPriceTotal == 0 ? 0 : ((netPriceTotal - netCostTotal) / netPriceTotal * 100).toFixed(0);

    $('#netMargin').text(netMargin + '%');

    if (netMargin / 100 < (mgmtAsmpts.min_mono_margin + mgmtAsmpts.min_mono_on_color_margin + mgmtAsmpts.min_color_margin) / 3) {
        $('#netMargin').addClass('warning');
    } else {
        $('#netMargin').removeClass('warning');
    }

    let nonNetTotal = 0;
    $.each(p_objects, function (index, device) {
        device = device.service;
        if (!device.is_non_network) {
            return;
        }

        nonNetTotal += (device.non_network_cost * device.number_printers_serviced);
    });
    $('#monthlyNonNetPrice').text('$' + addThousandsSeparator(nonNetTotal.toFixed(2)));

    let monthlyLease = 0;
    let equipmentBought = 0;
    $.each(proposal_purchase_items, function (index, item) {
        if (item.buy_or_lease === 'buy') {
            equipmentBought += parseFloat(item.proposed_cost);
        } else {
            monthlyLease += parseFloat(item.lease_payment);
        }
    });
    $('#monthly-lease').text('$' + addThousandsSeparator(monthlyLease.toFixed(2)));
    $('#monthly-lease').attr('val', addThousandsSeparator(monthlyLease.toFixed(2)));
    $('#equipment-bought').text('$' + addThousandsSeparator(equipmentBought.toFixed(2)));
    
    let monthlyCommission = 0;
    let monthlyMPSCommission = 0;
    let monthlyEQCommission = 0;
        $.each(proposal_service_items, function (index, item) {
            monthlyMPSCommission += parseFloat(item.estimated_commission);
        });

        $.each(proposal_purchase_items, function (index, item) {
            monthlyEQCommission += parseFloat(item.estimated_commission);
        });

        monthlyCommission = monthlyMPSCommission + monthlyEQCommission;

    $('#total-monthly-commission').text('$' + addThousandsSeparator(monthlyCommission.toFixed(2)));
    $('#monthly-commission').text('$' + addThousandsSeparator(monthlyMPSCommission.toFixed(2)));
    $('#monthly-eq-commission').text('$' + addThousandsSeparator(monthlyEQCommission.toFixed(2)));

    let totalPrice = netPriceTotal + nonNetTotal + monthlyLease;
    $('#monthlyTotalPrice').text('$' + addThousandsSeparator(totalPrice.toFixed(2)));
}
// eslint-disable-next-line no-unused-vars
function requestStreetFighter() {
    $.ajax({
        type: 'POST',
        cache: false,
        data: {
            'proposal_id': proposal_id
        },
        url: window.location.origin + '/proposal/requestStreetFighterPricing/'
    }).done(function (response) {
        alert(response);
    }).fail(function (response) {
        alert(response.responseText);
    });
}

function selectAccessory(devRow, accRow, accId) {
    let acc = accessories[accId];
    let quantity = parseInt($('#networkDevice-quantity').val());
    let outCost = acc.out_cost * (1 + mgmtAsmpts.accessory_inflate) * quantity;
    let msrp = acc.msrp_cost * quantity;
    $('#acc-out' + devRow + accRow).val(parseFloat(outCost).toFixed(2));
    $('#acc-msrp' + devRow + accRow).val(parseFloat(msrp).toFixed(2));
    updateDeviceTotalCosts(devRow);
}

function createCostInputGroup(containerClasses, id = '', dataItemType, dataPriceType) {
    let $container = $('<div>', { 'class': containerClasses });
    let $inputGroup = $('<div>', { 'class': 'input-group' });
    $inputGroup.append($('<span>', { 'class': 'input-group-label', text: '$' }));

    let $input = $('<input>', { id: id, 'class': 'input-group-field', type: 'number', step: '0.01', min: 0 });
    $input.attr('data-item-type', dataItemType);
    $input.attr('data-price-type', dataPriceType);
    $input.prop('disabled', true);

    $inputGroup.append($input);
    $container.append($inputGroup);
    return $container;
}

// eslint-disable-next-line no-unused-vars
function appendNewAccessory(sender, devRow) {
    let cellTwoClasses = 'cell medium-4 medium-offset-1';
    let accRow = $(sender).data('acc-row');

    let $row = $('<div>', { 'class': 'cell grid-x align-middle modal-row accessory-row' });
    $row.append($('<div>', { 'class': 'cell medium-3 medium-offset-1', text: 'Accessory'}));

    let $accSelectCell = $('<div>', { 'class': 'cell medium-8 medium-offset-1' });
    let $accSelectGroup = $('<div>', { 'class': 'select-group input-group' });
    let $accSelect = $('<select>');
    $accSelect.append($('<option>', { value: -1, text: 'Select Accessory' }).prop('hidden', true));
    $.each(accessories, function(key, accObj) {
        let $opt = $('<option>', { value: key, text: accObj.description });
        $accSelect.append($opt);
    });
    $accSelect.change(function () {
        selectAccessory(devRow, accRow, this.value);
    });
    $accSelectGroup.append($accSelect);
    $accSelectCell.append($accSelectGroup);
    $row.append($accSelectCell);

    let $outcostCell = createCostInputGroup(cellTwoClasses, 'acc-out' + devRow + accRow, 'acc', 'out');
    let $msrpCell = createCostInputGroup(cellTwoClasses, 'acc-msrp' + devRow + accRow, 'acc', 'msrp');
    $row.append($outcostCell);
    $row.append($msrpCell);
    $(sender).parent().before($row);
    $(sender).data('acc-row', accRow + 1);
}

// eslint-disable-next-line no-unused-vars
function appendNewDevice(sender) {
    let rowNum = $('[data-device-section]').length + 1;
    let leftCellClasses = 'cell grid-x align-middle modal-row';
    let inputCellClasses =  'cell medium-4 medium-offset-1';

    let $container = $('<div>', { 'class': 'grid-x' });
    $container.data('device-section', rowNum);

    let $row = $('<div>', { 'class': leftCellClasses });
    $row.append($('<div>', { 'class': 'cell medium-3 medium-offset-1', text: 'Device' }));

    let $devSelectCell = $('<div>', { 'class': 'cell medium-8 medium-offset-1' });
    let $devSelectGroup = $('<div>', { 'class': 'select-group input-group' });
    let $devSelect = $('<select>', { id: 'device-group-dropdown' + rowNum });
    $devSelect.change(function () {
        selectPurchaseDevice(this, rowNum);
    });
    setDeviceSelectOptions($devSelect, printer_costs);
    $devSelectGroup.append($devSelect);
    $devSelectCell.append($devSelectGroup);
    $row.append($devSelectCell);

    let $outcostCell = createCostInputGroup(inputCellClasses, 'dev', 'out');
    let $msrpCell = createCostInputGroup(inputCellClasses, 'dev', 'msrp');
    $row.append($outcostCell);
    $row.append($msrpCell);

    $container.append($row);
    $('[data-device-section=' + (rowNum - 1) + ']').after($row);
}

// Great America Leasing
function authenticate() {
    let authData = {
        'PartnerKey': 'dd6cdc54-2ce2-4459-880c-d6e2dd94cccf',
        'DealerKey': '9f81b9e5-4b6c-478b-9446-4a06f6b43128'
    };

    $.ajax({
        url: 'https://betaintegreat.greatamerica.com/api/Authentication',
        type: 'POST',
        contentType: 'application/json; charset=utf-8',
        data: JSON.stringify(authData),
        dataType: 'json',
        crossDomain: true,
        success: function (data) {
            localStorage.setItem('token', data.TokenID);
        }
    });

    token = localStorage.getItem('token');
}

// Great America Leasing
function getRates() {
    if (!cache[0]) {
        cache[0] = $.ajax({
            url: 'https://betaintegreat.greatamerica.com/api/RateFactor',
            type: 'GET',
            dataType: 'json',
            contentType: 'application/json; charset=utf-8',
            crossDomain: true,
            headers: {
                'Authorization': 'Basic ' + btoa(token + ':' + '')
            },
        });
    }
    return cache[0];
}

function getLeasingData() {
    if (!cache[1]) {
        cache[1] = $.ajax({
            async: false,
            url: window.location.origin + '/leasing-data/',
            type: 'GET',
            dataType: 'json',
            contentType: 'application/json; charset=utf-8',
            success: function(data) {
                var leasingData = [];

                for (var i = 0; i < data.length; i++) {
                    var leasing_company = data[i].leasing_company;
                    if (leasing_company === "Rental") {
                        continue;
                    }
                    var leasing_info = JSON.parse(data[i].leasing_info);

                    var lease_types = []
                    var lease_terms = []
                    for(var j = 0; j < leasing_info.length; j++) {
                        var lease_type = leasing_info[j].fields.lease_type;
                        var lease_term = leasing_info[j].fields.lease_term;

                        if (lease_types.indexOf(lease_type) == -1) {
                            lease_types.push(lease_type);
                        }

                        if (lease_terms.indexOf(lease_term) == -1) {
                            lease_terms.push(lease_term);
                        }
                    }

                    var dict = {
                        leasing_company: leasing_company,
                        lease_types: lease_types,
                        lease_terms: lease_terms
                    }
                    leasingData.push(dict);
                }

                var leasingCompanySelector = $('#leasing-company');

                $.each(leasingData, function (i, item) {
                    leasingCompanySelector.append($('<option>', {
                        value: i + 1,
                        text: item.leasing_company
                    }));
                });

                var leaseTypeSelector = $('#lease-type');

                $.each(leasingData[0].lease_types, function (i, item) {
                    leaseTypeSelector.append($('<option>', {
                        value: i + 1,
                        text: item
                    }));
                });

                var leaseTermSelector = $('#lease-term');

                $.each(leasingData[0].lease_terms, function (i, item) {
                    leaseTermSelector.append($('<option>', {
                        value: item,
                        text: item
                    }));
                });

                leasingCompanySelector.on('change', function () {
                    var leasingCompany = $(this).find("option:selected").text();

                    leaseTypeSelector.find('option').remove();
                    leaseTermSelector.find('option').remove();

                    for (var i in leasingData) {
                        if (leasingData[i].leasing_company == leasingCompany) {
                            // add the new lease types
                            $.each(leasingData[i].lease_types, function (i, item) {
                                leaseTypeSelector.append($('<option>', {
                                    value: i + 1,
                                    text: item
                                }));
                            });

                            // add the new lease terms
                            $.each(leasingData[i].lease_terms, function (i, item) {
                                leaseTermSelector.append($('<option>', {
                                    value: item,
                                    text: item
                                }));
                            });
                        }
                    }
                });
            }
        });
    }
    return cache[1];
}

// allow rental opton (gel 05-15-2020)
function getRentalData() {
    if (!cache[2]) {
        cache[2] = $.ajax({
            async: false,
            url: window.location.origin + '/leasing-data/',
            type: 'GET',
            dataType: 'json',
            contentType: 'application/json; charset=utf-8',
            success: function(data) {
                var leasingData = [];

                for (var i = 0; i < data.length; i++) {
                    var leasing_company = data[i].leasing_company;
                    if (leasing_company !== "Rental") {
                        continue;
                    }
                    var leasing_info = JSON.parse(data[i].leasing_info);

                    var lease_types = []
                    var lease_terms = []
                    for(var j = 0; j < leasing_info.length; j++) {
                        var lease_type = leasing_info[j].fields.lease_type;
                        var lease_term = leasing_info[j].fields.lease_term;

                        if (lease_types.indexOf(lease_type) == -1) {
                            lease_types.push(lease_type);
                        }

                        if (lease_terms.indexOf(lease_term) == -1) {
                            lease_terms.push(lease_term);
                        }
                    }

                    var dict = {
                        leasing_company: leasing_company,
                        lease_types: lease_types,
                        lease_terms: lease_terms
                    }
                    leasingData.push(dict);
                }

                var leasingCompanySelector = $('#rental-company');

                $.each(leasingData, function (i, item) {
                    leasingCompanySelector.append($('<option>', {
                        value: i + 1,
                        text: item.leasing_company
                    }));
                });

                var leaseTypeSelector = $('#rent-type');
                var leaseTermSelector = $('#rent-term');
                
                if (leasingData.length) {
                    $.each(leasingData[0].lease_types, function (i, item) {
                        leaseTypeSelector.append($('<option>', {
                            value: i + 1,
                            text: item
                        }));
                    });
    
                    $.each(leasingData[0].lease_terms, function (i, item) {
                        leaseTermSelector.append($('<option>', {
                            value: item,
                            text: item
                        }));
                    });
                }

                leasingCompanySelector.on('change', function () {
                    var leasingCompany = $(this).find("option:selected").text();

                    leaseTypeSelector.find('option').remove();
                    leaseTermSelector.find('option').remove();

                    for (var i in leasingData) {
                        if (leasingData[i].leasing_company == leasingCompany) {
                            // add the new lease types
                            $.each(leasingData[i].lease_types, function (i, item) {
                                leaseTypeSelector.append($('<option>', {
                                    value: i + 1,
                                    text: item
                                }));
                            });

                            // add the new lease terms
                            $.each(leasingData[i].lease_terms, function (i, item) {
                                leaseTermSelector.append($('<option>', {
                                    value: item,
                                    text: item
                                }));
                            });
                        }
                    }
                });
            }
        });
    }
    return cache[2];
}

function calculateLeasePayment() {
    var leasing_company = $('#leasing-company option:selected').text();
    var company_id = $('#rental-company-id').val();
    var lease_type = $('#lease-type option:selected').text();
    var lease_term = $('#lease-term option:selected').text();
    var bundled_amt = $('#bundledAmt').val();
    var lease_buyout = $('#leaseBuyout').val();
    var lease_purchase_price = $('#leasePurchasePrice').val();
    var lease_select_type = $('#leaseSelectType').val();
    if ($('#leaseSelectType').val() === "2") {
        $('#bundledSection').show()
    } else {
        $('#bundledSection').hide()
    };

    let lease_data = {
        leasing_company: leasing_company,
        lease_type: lease_type,
        lease_term: lease_term,
        lease_select_type: lease_select_type,
        bundled_amt: bundled_amt,
        lease_buyout: lease_buyout,
        lease_purchase_price: lease_purchase_price,
        company_id
    }

    $.ajax({
        url: window.location.origin + '/calculate-lease-payment/',
        type: 'POST',
        data: {
            lease_data: JSON.stringify(lease_data)
        },
        dataType: 'json',
        success: function(data) {
            $('#monthly-payment').val(data.lease_payment);
        }
    });
}
 
// allow Rent option (gel 05-15-2020)
function calculateRentPayment() {
    var leasing_company = $('#rental-company option:selected').text();
    var company_id = $('#rental-company-id').val();
    var lease_type = $('#rent-type option:selected').text();
    var lease_term = $('#rent-term option:selected').text();
    var bundled_amt = $('#rent-bundledAmt').val();
    var lease_buyout = $('#rentBuyout').val();
    var lease_purchase_price = $('#rentPurchasePrice').val();
    var lease_select_type = $('#rentSelectType').val();

    if ($('#rentSelectType').val() === "2") {
        $('#rentbundledSection').show()
    } else {
        $('#rentbundledSection').hide()
    }; 

    let lease_data = {
        leasing_company: leasing_company,
        lease_type: lease_type,
        lease_term: lease_term,
        lease_select_type: lease_select_type,
        bundled_amt: bundled_amt,
        lease_buyout: lease_buyout,
        lease_purchase_price: lease_purchase_price,
        company_id
    }

    $.ajax({
        url: window.location.origin + '/calculate-lease-payment/',
        type: 'POST',
        data: {
            lease_data: JSON.stringify(lease_data)
        },
        dataType: 'json',
        success: function(data) {
            $('#rent-monthly-payment').val(data.lease_payment);
        }
    });
}

// common code used to update bundled lease information
function updateBundledMono() {
    $('#bundled-mono-monthly').val((($('#bundled-mono-price').val()*1)*$('#bundled-monthly-mono-pages').val()).toFixed(2));
    $('#bundledAmt').val(($('#bundled-mono-monthly').val()*1+$('#bundled-color-monthly').val()*1).toFixed(2));    
}

function updateBundledColor() {
    $('#bundled-color-monthly').val((($('#bundled-color-price').val()*1) * $('#bundled-monthly-color-pages').val() ) .toFixed(2) );
    $('#bundledAmt').val(($('#bundled-mono-monthly').val()*1 + $('#bundled-color-monthly').val()*1).toFixed(2));
}

$('#leasing-company').on('change', function () {
    calculateLeasePayment();
});

$('#lease-type').on('change', function () {
    calculateLeasePayment();
});

$('#lease-term').on('change', function () {
    calculateLeasePayment();
});

$('#leaseSelectType').on('change', function () {
    // Initialize bundled values, call update functions (GEL 06-20-2020)
    if ($('#leaseSelectType').val() === "2") {
        $('#bundledSection').show();
        $('#bundled-monthly-mono-pages').val($('#total-monthly-mono-pages').val()*1);
        $('#bundled-monthly-color-pages').val($('#total-monthly-color-pages').val()*1);
    } else {
        $('#bundled-monthly-mono-pages').val(0);
        $('#bundled-monthly-color-pages').val(0);
        $('#bundled-mono-monthly').val(0);
        $('#bundled-color-monthly').val(0);
        $('#bundledSection').hide()
    };
    updateBundledMono();
    updateBundledColor();
    calculateLeasePayment();
});

$('#rent-term').on('change', function () {
    calculateRentPayment();
});

$('#rentSelectType').on('change', function () {
    calculateRentPayment();
});
// Synchronize the page counts with number of devices (GEL 2020-04-04)
$('#networkDevice-quantity').on('change', function () {
    let quantity = parseInt($('#networkDevice-quantity').val());

    let total_monthly_mono = quantity * parseInt($('#def-monthly-mono-pages').val());
    $('#total-monthly-mono-pages').val(total_monthly_mono);
    $('#bundled-monthly-mono-pages').val(total_monthly_mono);
    $('#rent-bundled-monthly-mono-pages').val(total_monthly_mono);

    let total_monthly_color = quantity * parseInt($('#def-monthly-color-pages').val());
    $('#total-monthly-color-pages').val(total_monthly_color);
    $('#bundled-monthly-color-pages').val(total_monthly_color);
    $('#rent-bundled-monthly-color-pages').val(total_monthly_color);

    $('#total-monthly-pages').val(total_monthly_mono + total_monthly_color)
});
// Synchronize the bundled pages with any changes on the equipment page.
// Exclude bundled values from reset since lease is already calculated (GEL 06-20-2020)
$('#total-monthly-mono-pages').on('change', function () {
    $('#rent-bundled-monthly-mono-pages').val($('#total-monthly-mono-pages').val()*1);
});
$('#total-monthly-color-pages').on('change', function () {
    $('#rent-bundled-monthly-color-pages').val($('#total-monthly-color-pages').val()*1);
});

// On change of lease included pages, update other dependant calculations
// Memo: take into account moving pages around.
$('#lease-term').on('change', function () {
    let equipprice = $('#equipment-purchase-price').val()*1;
    let monthlymono = $('#included-mono-monthly').val()*1;
    let monthlycolor = $('#included-color-monthly').val()*1;
    let leaseterm = $('#lease-term option:selected').val()*1;
    let leasebuyout = $('#leaseBuyout').val()*1;
    let newpurchaseprice = equipprice + leasebuyout + leaseterm * (monthlymono + monthlycolor);
    $('#leasePurchasePrice').val( newpurchaseprice.toFixed(2) );
    calculateLeasePayment();
});
$('#included-monthly-mono-pages').on('change keyup', function () {
    $('#included-mono-monthly').val((($('#included-mono-price').val()*1) * $('#included-monthly-mono-pages').val()*1).toFixed(2));

    let equipprice = $('#equipment-purchase-price').val()*1;
    let monthlymono = $('#included-mono-monthly').val()*1;
    let monthlycolor = $('#included-color-monthly').val()*1;
    let leaseterm = $('#lease-term option:selected').val()*1;
    let leasebuyout = $('#leaseBuyout').val()*1;
    let newpurchaseprice = equipprice + leasebuyout + leaseterm * (monthlymono + monthlycolor);

    $('#includedAmt').val((monthlymono + monthlycolor).toFixed(2));
    $('#leasePurchasePrice').val(newpurchaseprice.toFixed(2));

    $('#bundled-monthly-mono-pages').val($('#def-monthly-mono-pages').val()*1 - $('#included-monthly-mono-pages').val()*1);
    if ($('#bundled-monthly-mono-pages').val()*1 < 0) {
        $('#bundled-monthly-mono-pages').val('0')
    };
    
    updateBundledMono();
    calculateLeasePayment();
});
$('#included-monthly-color-pages').on('change keyup', function () {
    $('#included-color-monthly').val((($('#included-color-price').val()*1) * $('#included-monthly-color-pages').val()*1).toFixed(2));

    let equipprice = $('#equipment-purchase-price').val()*1;
    let monthlymono = $('#included-mono-monthly').val()*1;
    let monthlycolor = $('#included-color-monthly').val()*1;
    let leaseterm = $('#lease-term option:selected').val()*1;
    let leasebuyout = $('#leaseBuyout').val()*1;
    let newpurchaseprice = equipprice + leasebuyout + leaseterm * (monthlymono + monthlycolor);

    $('#includedAmt').val((monthlymono + monthlycolor).toFixed(2));
    $('#leasePurchasePrice').val(newpurchaseprice.toFixed(2));

    $('#bundled-monthly-color-pages').val($('#def-monthly-color-pages').val()*1 - $('#included-monthly-color-pages').val()*1);
    if ($('#bundled-monthly-color-pages').val()*1 < 0) {
        $('#bundled-monthly-color-pages').val('0')
    };
    
    updateBundledColor();
    calculateLeasePayment();
});
$('#included-mono-price').on('change keyup', function () {
    $('#included-mono-monthly').val((($('#included-mono-price').val()*1) * $('#included-monthly-mono-pages').val()*1).toFixed(2));

    let equipprice = $('#equipment-purchase-price').val()*1;
    let monthlymono = $('#included-mono-monthly').val()*1;
    let monthlycolor = $('#included-color-monthly').val()*1;
    let leaseterm = $('#lease-term option:selected').val()*1;
    let leasebuyout = $('#leaseBuyout').val()*1;
    let newpurchaseprice = equipprice + leasebuyout + leaseterm * (monthlymono + monthlycolor);

    $('#includedAmt').val((monthlymono + monthlycolor).toFixed(2));
    $('#leasePurchasePrice').val(newpurchaseprice.toFixed(2));
    
    updateBundledMono()
    calculateLeasePayment();
});
$('#included-color-price').on('change keyup', function () {
    $('#included-color-monthly').val((($('#included-color-price').val()*1) * $('#included-monthly-color-pages').val()*1).toFixed(2));

    let equipprice = $('#equipment-purchase-price').val()*1;
    let monthlymono = $('#included-mono-monthly').val()*1;
    let monthlycolor = $('#included-color-monthly').val()*1;
    let leaseterm = $('#lease-term option:selected').val()*1;
    let leasebuyout = $('#leaseBuyout').val()*1;
    let newpurchaseprice = equipprice + leasebuyout + leaseterm * (monthlymono + monthlycolor);

    $('#includedAmt').val((monthlymono + monthlycolor).toFixed(2));
    $('#leasePurchasePrice').val(newpurchaseprice.toFixed(2));

    updateBundledMono()
    calculateLeasePayment();
});
// end of included section

// On change of lease estimated monthly page count, update other dependant calculations
$('#bundled-monthly-mono-pages').on('change', function () {
    updateBundledMono();
    calculateLeasePayment();
});
$('#bundled-monthly-color-pages').on('change', function () {
    updateBundledColor();
    calculateLeasePayment();
});

// On change of rent estimated monthly page count, update other dependant calculations
$('#rent-bundled-monthly-mono-pages').on('change', function () {
    $('#total-monthly-mono-pages').val($('#rent-bundled-monthly-mono-pages').val()*1);
    $('#rent-bundled-mono-monthly').val((($('#rent-recommended-mono-sales-price2').val()*1 - $('#rent-bundled-mono-price').val()*1)*$('#bundled-monthly-mono-pages').val()).toFixed(2));
    $('#rent-bundledAmt').val(($('#rent-bundled-mono-monthly').val()*1+$('#rent-bundled-color-monthly').val()*1).toFixed(2));
    $('#total-monthly-pages').val($('#rent-bundled-monthly-mono-pages').val()*1+$('#rent-bundled-monthly-color-pages').val()*1);
    calculateLeasePayment();
});
$('#rent-bundled-monthly-color-pages').on('change', function () {
    $('#total-monthly-color-pages').val($('#rent-bundled-monthly-color-pages').val()*1);
    $('#rent-bundled-color-monthly').val((($('#rent-recommended-color-sales-price2').val()*1 - $('#rent-bundled-color-price').val()*1)*$('#bundled-monthly-color-pages').val()).toFixed(2));
    $('#rent-bundledAmt').val(($('#rent-bundled-mono-monthly').val()*1+$('#rent-bundled-color-monthly').val()*1).toFixed(2));
    $('#total-monthly-pages').val($('#rent-bundled-monthly-mono-pages').val()*1+$('#rent-bundled-monthly-color-pages').val()*1);
    calculateLeasePayment();
});

// On change of lease bundled price, update other dependant calculations
$('#bundled-mono-price').on('change', function () {
    $('#proposed-mono-sales').val(($('#bundled-mono-price').val()*1).toFixed(4));
    $('#bundled-mono-monthly').val((($('#recommended-mono-sales-price2').val()*1 - $('#bundled-mono-price').val()*1)*$('#bundled-monthly-mono-pages').val()).toFixed(2));
    $('#bundledAmt').val(($('#bundled-mono-monthly').val()*1+$('#bundled-color-monthly').val()*1).toFixed(2));
    calculateLeasePayment();
});
$('#bundled-color-price').on('change', function () {
    $('#proposed-color-sales').val(($('#bundled-color-price').val()*1).toFixed(4));
    $('#bundled-color-monthly').val((($('#recommended-color-sales-price2').val()*1 - $('#bundled-color-price').val()*1)*$('#bundled-monthly-color-pages').val()).toFixed(2));
    $('#bundledAmt').val(($('#bundled-mono-monthly').val()*1+$('#bundled-color-monthly').val()*1).toFixed(2));
    calculateLeasePayment();
});

// On change of rent bundled price, update other dependant calculations
$('#rent-bundled-mono-price').on('change', function () {
    $('#proposed-mono-sales').val(($('#rent-bundled-mono-price').val()*1).toFixed(4));
    $('#rent-bundled-mono-monthly').val((($('#rent-recommended-mono-sales-price2').val()*1 - $('#rent-bundled-mono-price').val()*1)*$('#bundled-monthly-mono-pages').val()).toFixed(2));
    $('#rent-bundledAmt').val(($('#rent-bundled-mono-monthly').val()*1+$('#rent-bundled-color-monthly').val()*1).toFixed(2));
    calculateRentPayment();
});
$('#rent-bundled-color-price').on('change', function () {
    $('#proposed-color-sales').val(($('#rent-bundled-color-price').val()*1).toFixed(4));
    $('#rent-bundled-color-monthly').val((($('#rent-recommended-color-sales-price2').val()*1 - $('#rent-bundled-color-price').val()*1)*$('#bundled-monthly-color-pages').val()).toFixed(2));
    $('#rent-bundledAmt').val(($('#rent-bundled-mono-monthly').val()*1+$('#rent-bundled-color-monthly').val()*1).toFixed(2));
    calculateRentPayment();
});

// On change of bundled lease amount, update other dependant calculations
$('#bundled-mono-monthly').on('change', function () {
    $('#bundled-mono-price').val(( $('#recommended-mono-sales-price2').val()*1 +  $('#bundled-mono-monthly').val()/$('#bundled-monthly-mono-pages').val()).toFixed(4));
    $('#proposed-mono-sales').val(($('#bundled-mono-price').val()*1).toFixed(4));
    $('#bundledAmt').val(($('#bundled-mono-monthly').val()*1+$('#bundled-color-monthly').val()*1).toFixed(2));
    calculateLeasePayment();
});
$('#bundled-color-monthly').on('change', function () {
    $('#bundled-color-price').val(( $('#recommended-color-sales-price2').val()*1 +  $('#bundled-color-monthly').val()/$('#bundled-monthly-color-pages').val()).toFixed(4));
    $('#proposed-color-sales').val(($('#bundled-color-price').val()*1).toFixed(4));
    $('#bundledAmt').val(($('#bundled-mono-monthly').val()*1+$('#bundled-color-monthly').val()*1).toFixed(2));
    calculateLeasePayment();
});

// On change of bundled rent amount, update other dependant calculations
$('#rent-bundled-mono-monthly').on('change', function () {
    $('#rent-bundled-mono-price').val(( $('#rent-recommended-mono-sales-price2').val()*1 +  $('#rent-bundled-mono-monthly').val()/$('#bundled-monthly-mono-pages').val()).toFixed(4));
    $('#proposed-mono-sales').val(($('#rent-bundled-mono-price').val()*1).toFixed(4));
    $('#rent-bundledAmt').val(($('#rent-bundled-mono-monthly').val()*1+$('#rent-bundled-color-monthly').val()*1).toFixed(2));
    calculateRentPayment();
});
$('#rent-bundled-color-monthly').on('change', function () {
    $('#bundled-color-price').val(( $('#rent-recommended-color-sales-price2').val()*1 +  $('#rent-bundled-color-monthly').val()/$('#bundled-monthly-color-pages').val()).toFixed(4));
    $('#proposed-color-sales').val(($('#rent-bundled-color-price').val()*1).toFixed(4));
    $('#rent-bundledAmt').val(($('#rent-bundled-mono-monthly').val()*1+$('#rent-bundled-color-monthly').val()*1).toFixed(2));
    calculateRentPayment();
});


/* TODO: Save this for Great America Leasing integration

$('#lease-type').on('change', function () {
    getRates().done(function (data) {
        let monthlyPayment = calculateMonthlyPayment(data);
        $('#monthly-payment').val(monthlyPayment.toFixed(2));
    });
});

$('#lease-term').on('change', function () {
    getRates().done(function (data) {
        let monthlyPayment = calculateMonthlyPayment(data);
        $('#monthly-payment').val(monthlyPayment.toFixed(2));
    });
});

function calculateMonthlyPayment(data) {
    let printerPrice = parseInt($('#leasePurchasePrice').val());
    let leaseType = $('#lease-type').val();
    let term = parseInt($('#lease-term').val());

    let rateCardIndex = 0;
    for (let i = 0; i < data.RateFactorInfo.length; i++) {
        if (data.RateFactorInfo[i].RateCardName.includes(leaseType)) {
            rateCardIndex = i;
            break;
        }
    }

    let rateFactorIndex = 0;
    let rateFactors = data.RateFactorInfo[rateCardIndex].RateFactors;
    for (let i = 0; i < rateFactors.length; i++) {
        if (parseInt(rateFactors[i].Term) === term) {
            rateFactorIndex = i;
            break;
        }
    }

    let rangeIndex = null;
    let ranges = rateFactors[rateFactorIndex].Values;
    for (let i = 1; i < ranges.length; i++) {
        let startRange = parseInt(ranges[i - 1].RangeStart);
        let endRange = parseInt(ranges[i].RangeStart);

        if ((printerPrice >= startRange) && (printerPrice <= endRange)) {
            rangeIndex = i - 1;
            break;
        }
    }
    if (rangeIndex === null) {
        rangeIndex = ranges.length - 1;
    }

    return parseFloat(printerPrice * ranges[rangeIndex].Rate);
}
*/

function updatePObjects() {
    for(var i = 0; i < proposal_service_items.length; i++){
        let current_item =  proposal_service_items[i];
        if (!p_objects[current_item.id]) {
            p_objects[current_item.id] = {
                service: current_item,
                equipment: {}, //fill up later
                mono_tier: current_item.tier_level_mono,
                color_tier: current_item.tier_level_color
            };
        }
    }
}
