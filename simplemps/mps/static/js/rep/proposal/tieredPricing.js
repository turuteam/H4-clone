'use strict';
/* global p_objects */
/* global mgmtAsmpts */
/* global proposal_id */
/* global addThousandsSeparator */
/* global stripSpecialChars */

const dummy_row = `
<tr class="dummy-row">
    <td align="center" colspan="14"> No data in this tier </td>
</tr>`;


$(document).ready(function () {
    $('.section-table td:contains(\'28%\')').css('background-color', 'var(--mps-banana)');
    $('.section-table td:contains(\'18%\')').css('background-color', 'var(--mps-stoplight)');
    $('.section-table td:contains(\'30%\')').css('background-color', 'var(--mps-leaf)');
    $('.section-table td:contains(\'31%\')').css('background-color', 'var(--mps-leaf)');
    $('#previous-page').on('click', function () {
        window.location.href = window.location.origin + '/proposal/details/' + proposal_id;
    });



    $('table.connectedSortable.color > tbody').sortable({
        connectWith: '.connectedSortable.color > tbody', //add class here
        items: 'tr.moveable',
        appendTo: 'parent',
        helper: 'clone',
        cursor: 'move',
        zIndex: 999990,
        receive: function () {
            update_moved_item_tier(this);
        }
    });

    $('table.connectedSortable.mono > tbody').sortable({
        connectWith: '.connectedSortable.mono > tbody', //add class here
        items: 'tr.moveable',
        appendTo: 'parent',
        helper: 'clone',
        cursor: 'move',
        zIndex: 999990,
        receive: function () {
            update_moved_item_tier(this);
        }
    });

    createPrinterRow();
    footerCalculate('bw1', update_row_in_summary_table);
    footerCalculate('bw2', update_row_in_summary_table);
    footerCalculate('bw3', update_row_in_summary_table);
    footerCalculate('bw4', update_row_in_summary_table);
    footerCalculate('color1', update_row_in_summary_table);
    footerCalculate('color2', update_row_in_summary_table);
    footerCalculate('color3', update_row_in_summary_table);

    if (mgmtAsmpts.allow_tco) {
      $('#tco-button3').show();
    } else {
      $('#tco-button3').hide();
    }
});

function update_moved_item_tier(moved_item) {
    let addedTo = $(moved_item).closest('table.section-table')[0].id;
    let rows = moved_item.querySelectorAll('tr.section-content');
    let removedFrom;
    let item_moved;
    // console.log(p_objects[this.querySelectorAll('tr')[2].id].tier);
    // console.log(addedTo[0].id);
    //removeFrom won't work very well, we need to just check the p_objects to see which one it came from, and then update it's item
    //alert("The ajax should be called for adding to " + addedTo.attr("id") + " and removing from " + removedFrom.attr("id"));


    //we need to figure out where the object is removed from so we can
    //properly update its tier and the table it came from
    let updating = 'mono';
    for (let i = 0; i < rows.length; i++) {
        let id = parseInt(rows[i].id);
        let p_object = p_objects[id];
        if (addedTo.includes('color')) {
            if (p_object.color_tier != addedTo) {
                updating = 'color';
                removedFrom = p_object.color_tier;
                p_object.color_tier = addedTo;
                item_moved = id;
                break;
            }
        } else {
            if (p_object.mono_tier != addedTo) {
                removedFrom = p_object.mono_tier;
                p_object.mono_tier = addedTo;
                item_moved = id;
                break;
            }
        }
    }
    let data = {
        tier: addedTo,
        printer_id: item_moved,
        printer_color_updated: updating
    };
    $.ajax({
        type: 'POST',
        cache: false,
        data: {
            data: JSON.stringify(data)
        },
        url: window.location.origin + '/proposal/pricing/' + proposal_id + '/update_tier/'
    }).done(function () {
        toggle_dummy_row(removedFrom);
        toggle_dummy_row(addedTo);
        footerCalculate(removedFrom, update_row_in_summary_table);
        footerCalculate(addedTo, update_row_in_summary_table);
    }).fail(function (error) {
        console.log(error);
    });
}

function has_dummy_row(tier) {
    return $(`table#${tier} > tbody > .dummy-row`).length > 0;
}

function should_have_dummy_row(tier) {
    let num_rows = $(`table#${tier} > tbody > tr`).length;
    let dummy_row_add = has_dummy_row(tier) ? 1 : 0;
    return num_rows - dummy_row_add <= 0;
}

function toggle_dummy_row(tier) {
    if (should_have_dummy_row(tier)) {
        add_dummy_row(tier);
    } else {
        remove_dummy_row(tier);
    }
}

function add_dummy_row(tier) {
    $(`table#${tier} > tbody`).append(dummy_row);
}

function remove_dummy_row(tier) {
    $(`table#${tier} > tbody > .dummy-row`).remove();
}

let proposedCPPTimer;
let changedCPP;
function changeProposedCPP () {
    let tier_id = changedCPP.parent().attr('id').split('_')[0];
    let new_proposed_cpp = parseFloat(changedCPP.val());
    let proposed_cpp = changedCPP.parent().attr('id');
    if (isNaN(new_proposed_cpp)) {
        // if there is no proposed cpp, use the tier's overage rate
        let temp_cpp = parseFloat(stripSpecialChars($('#' + tier_id + '_overage_cpp').text()));
        update_costs_in_table_with_new_cpp(tier_id, temp_cpp);
    } else {
        update_costs_in_table_with_new_cpp(tier_id, new_proposed_cpp);
    }
    let data = {
        proposal_id: proposal_id,
        proposed_cpp: proposed_cpp,
        value: new_proposed_cpp
    };
    $.ajax({
        type: 'POST',
        cache: false,
        data: {
            data: JSON.stringify(data)
        },
        url: window.location.origin + '/proposal/saveProposedCPP/'
    });
}
$('.proposed-cpp input').on('keyup change', function () {
    changedCPP = $(this);
    clearTimeout(proposedCPPTimer);
    proposedCPPTimer = setTimeout(changeProposedCPP,500);
});


function update_costs_in_table_with_new_cpp(tier) {
    $('#' + tier + ' > tbody > tr').each(function () {
        let service_item_id = $(this).attr('id');
        if (service_item_id) {
            let service = p_objects[service_item_id].service;
            update_costs_in_row($(this), service, tier);
        }
    });
    footerCalculate(tier, update_row_in_summary_table);
}

function get_proposed_cpp(tier, overage_cpp = 0) {
    let prop_cpp = parseFloat($('#Sum-table').find(`#sum_${tier}`).find('.proposed-cpp').find('input').val());
    if (isNaN(prop_cpp)) {
        if (overage_cpp == 0){
            // if there is no proposed cpp, use the tier's overage rate
            prop_cpp = parseFloat(stripSpecialChars($('#' + tier + '_overage_cpp').text()));
        } else {
            prop_cpp = overage_cpp;
        }
    }
    return prop_cpp;
}


//This will take in an actual jquery row
function createPrinterRow() {
    let all_tiers = new Set(['bw1', 'bw2', 'bw3', 'bw4', 'color1', 'color2', 'color3']);
    all_tiers.forEach((tier) => {
        add_dummy_row(tier);
    });
    for (let key in p_objects) {
        if (p_objects.hasOwnProperty(key)) {
            appendToTierTable(key);
        }
    }

}

//currying this because footer won't change
function setRowToUpdate(footer) {
    function updateRow(column, value) {
        footer.find(column).text(addThousandsSeparator(value));
    }
    return updateRow;
}

function setRow(row) {
    function findInRow(rowClass) {
        return parseFloat(stripSpecialChars(row.find(rowClass).text()));
    }
    return findInRow;
}

function footerCalculate(tableID, callback) {
    let section_table_footer = $('#' + tableID).find('tfoot');
    let updateRow = setRowToUpdate(section_table_footer);
    let footer_values = {
        total_base_volume: 0,
        total_base_rate: 0,
        total_overage_volume: 0,
        total_overage_rate: 0,
        total_supply_cost: 0,
        total_revenue: 0,
        total_service_cost: 0,
        total_monthly_cost: 0,
        total_gp1: 0,
        total_margin: 0
    };

    $('#' + tableID + ' > tbody > tr').each(function () {
        let findInRow = setRow($(this));

        let base_volume = findInRow('.base-volume');
        let base_rate = findInRow('.base-rate');
        let overage_cpp = findInRow('.overage-cpp');
        let overage_volume = findInRow('.overage-volume');
        let supply_cost = findInRow('.supply-cost');
        let revenue = findInRow('.total-revenue');
        let service_cost = findInRow('.service-cost');
        let monthly_cost = findInRow('.monthly-cost');
        let margin = findInRow('.margin1');
        margin = isNaN(margin) ? revenue - monthly_cost : margin;
        let gp1 = findInRow('.gp1');

        supply_cost = mgmtAsmpts.contract_service_type == 'service_only' ? 0 : supply_cost;
        service_cost = mgmtAsmpts.contract_service_type == 'supplies_only' ? 0 : service_cost;

        footer_values['total_margin'] += margin;
        footer_values['total_gp1'] += gp1;
        footer_values['total_monthly_cost'] += monthly_cost;
        footer_values['total_service_cost'] += service_cost;
        footer_values['total_revenue'] += revenue;
        footer_values['total_base_volume'] += base_volume;
        footer_values['total_base_rate'] += base_rate;
        footer_values['total_supply_cost'] += supply_cost;
        footer_values['total_overage_volume'] += overage_volume;
        footer_values['total_overage_rate'] += overage_cpp * overage_volume;
    });

    footer_values['total_monthly_volume'] = footer_values['total_base_volume'] + footer_values['total_overage_volume'];
    footer_values['total_service_cpp'] = footer_values['total_service_cost'] / footer_values['total_monthly_volume'];
    footer_values['average_overage_cpp'] = footer_values['total_overage_rate'] / footer_values['total_overage_volume'];
    footer_values['toner_coverage'] = footer_values['total_supply_cost'] / footer_values['total_monthly_volume'];
    footer_values['total_cpp'] = footer_values['toner_coverage'] + footer_values['total_service_cpp'];
    footer_values['gp2'] = footer_values['total_gp1'] / footer_values['total_revenue'] * 100;
    footer_values['margin_percentage'] = footer_values['total_margin'] / footer_values['total_revenue'];
    //TODO: Update formats
    updateRow('.base-volume', format_volume(footer_values['total_base_volume']));
    updateRow('.base-rate', format_cost(footer_values['total_base_rate']));
    updateRow('.overage-volume', format_volume(footer_values['total_overage_volume']));
    updateRow('.overage-cpp', format_cpp(footer_values['average_overage_cpp']));
    updateRow('.total-revenue', format_cost(footer_values['total_revenue']));
    updateRow('.toner-coverage', format_cpp(footer_values['toner_coverage']));
    updateRow('.service-cost', mgmtAsmpts.contract_service_type != 'supplies_only' ? format_cost(footer_values['total_service_cost']) : '-');
    updateRow('.service-cpp', format_cpp(footer_values['total_service_cpp']));
    updateRow('.total-cpp', format_cpp(footer_values['total_cpp']));
    updateRow('.supply-cost', mgmtAsmpts.contract_service_type != 'service_only' ? format_cost(footer_values['total_supply_cost']) : '-');
    updateRow('.monthly-cost', format_cost(footer_values['total_monthly_cost']));
    updateRow('.gp1', format_cost(footer_values['total_gp1']));
    updateRow('.gp2', format_volume(footer_values['gp2']));
    updateRow('.margin1', format_cost(footer_values['total_margin']));
    updateRow('.margin2', format_percentage(footer_values['margin_percentage']));
    if (callback) {
        callback(tableID, footer_values);
    }

}

function update_row_in_summary_table(tier, footer_values) {
    let row = $('table#Sum-table').find('#sum_' + tier);
    let updateRow = setRowToUpdate(row);

    let margin = footer_values['total_revenue'] - footer_values['total_monthly_cost'];

    //TODO: proposed_margin
    let proposed_margin;
    if (mgmtAsmpts.contract_service_type == 'service_only') {
        proposed_margin = mgmtAsmpts.target_margin_service;
    } else if (mgmtAsmpts.contract_service_type == 'supplies_only') {
        proposed_margin = mgmtAsmpts.target_margin_toner;
    } else {
        proposed_margin = (footer_values['total_supply_cost'] / footer_values['total_monthly_cost']) * mgmtAsmpts.target_margin_toner + (footer_values['total_service_cost'] / footer_values['total_monthly_cost']) * mgmtAsmpts.target_margin_service;
    }

    updateRow('.base-volume', format_volume(footer_values['total_base_volume']));
    updateRow('.base-rate', format_cost(footer_values['total_base_rate']));
    updateRow('.overage-volume', format_volume(footer_values['total_overage_volume']));
    updateRow('.overage-cpp', format_cpp(footer_values['average_overage_cpp']));
    updateRow('.total-revenue', format_cost(footer_values['total_revenue']));
    updateRow('.supply-cost', mgmtAsmpts.contract_service_type != 'service_only' ? format_cost(footer_values['total_supply_cost']) : '-');
    updateRow('.service-cost', mgmtAsmpts.contract_service_type != 'supplies_only' ? format_cost(footer_values['total_service_cost']) : '-');
    updateRow('.monthly-cost', format_cost(footer_values['total_monthly_cost']));
    updateRow('.margin1', format_cost(margin));
    updateRow('.margin2', format_percentage(footer_values['margin_percentage']));
    updateRow('.proposed-margin', format_percentage(proposed_margin));

    footerCalculate('Sum-table');
}

//Excel calculations. Maybe move into another file
function update_costs_in_row(row, service, tier) {
    let p_color = tier.includes('color') ? 'color' : 'bw';
    let base_volume;
    let base_rate;
    let total_volume;
    let toner_coverage_55;

    if (p_color === 'bw') {
        base_volume = service.base_volume_mono;
        base_rate = service.base_rate_mono;
        total_volume = service.total_mono_pages;
        toner_coverage_55 = service.mono_cpp; //TODO: this needs to be for mono


    } else {
        base_volume = service.base_volume_color;
        base_rate = service.base_rate_color;
        total_volume = service.total_color_pages;
        toner_coverage_55 = service.color_cpp; //TODO: this needs to be color
    }
    
    let overage_volume = calculate_overage_volume(total_volume, base_volume);
    let service_cpp = calculate_service_cpp(service);
    let service_cost = service_cpp * total_volume;
    let total_cpp_cost = calculate_total_cpp_cost(service_cpp, toner_coverage_55);
    let supply_cost = calculate_supply_cost(toner_coverage_55, total_volume);

    supply_cost = mgmtAsmpts.contract_service_type == 'service_only' ? 0 : supply_cost;

    let overage_cpp = calculate_overage_cpp(overage_volume, base_rate, supply_cost, service_cost);
    let revenue_cpp = get_proposed_cpp(tier, overage_cpp);
    let total_revenue = calculate_total_revenue_excel(revenue_cpp, overage_volume, base_rate);

    let monthly_cost = calculate_monthly_cost(supply_cost, service_cost);
    let gp_total = calculate_gp(total_revenue, monthly_cost);
    let gp_percentage = calculate_gp_percentage(gp_total, total_revenue) * 100;

    row.find('.base-volume').html(base_volume);
    row.find('.base-rate').html(base_rate);
    row.find('.overage-volume').html(overage_volume);
    row.find('.overage-cpp').html(overage_cpp.toFixed(4));
    row.find('.total-revenue').html(total_revenue.toFixed(2));
    row.find('.toner-coverage').html(toner_coverage_55.toFixed(4));
    row.find('.service-cpp').html(service_cpp.toFixed(4));
    row.find('.total-cpp-cost').html(total_cpp_cost.toFixed(4));
    row.find('.supply-cost').html(mgmtAsmpts.contract_service_type != 'service_only' ? supply_cost.toFixed(2) : '-');
    row.find('.service-cost').html(mgmtAsmpts.contract_service_type != 'supplies_only' ? service_cost.toFixed(2) : '-');
    row.find('.monthly-cost').html(monthly_cost.toFixed(2));
    row.find('.gp1').html(gp_total.toFixed(2));
    row.find('.gp2').html(gp_percentage.toFixed(0));
}


function appendToTierTable(id) {
    let item = p_objects[id];
    let service = item.service;

    if(item.mono_tier !== null && item.mono_tier !== 'none') {
        let table = $(`table#${item.mono_tier} > tbody`);
        if ($(table).find(".dummy-row")) {
            remove_dummy_row(item.mono_tier);
        }
        table.append(`<tr class="section-content moveable" id="${id}" data-id="${id}">`);

        let row = table.find(`#${id}`);
        row.append(`
            <td>${service.short_model}</td>
            <td class="base-volume"></td>
            <td class="base-rate"></td>
            <td class="overage-volume"></td>
            <td class="overage-cpp hide"></td>
            <td class="total-revenue"></td>
            <td class="toner-coverage"></td>
            <td class="service-cpp"></td>
            <td class="total-cpp-cost"></td>
            <td class="supply-cost"></td>
            <td class="service-cost"></td>
            <td class="monthly-cost"></td>
            <td class="gp1"></td>
            <td class="gp2"></td></tr>`);
        update_costs_in_row(row, service, item.mono_tier);
        footerCalculate(item.mono_tier, update_row_in_summary_table);
    }

    if (item.color_tier !== null && item.color_tier !== 'none') {
        let table = $(`table#${item.color_tier} > tbody`);
        if ($(table).find(".dummy-row")) {
            remove_dummy_row(item.color_tier);
        }
        //console.log(item);
        table.append(`<tr class="section-content moveable" id="${id}" data-id="${id}">`);

        let row = table.find(`#${id}`);
        row.append(`
            <td>${service.short_model}</td>
            <td class="base-volume"></td>
            <td class="base-rate"></td>
            <td class="overage-volume"></td>
            <td class="overage-cpp hide"></td>
            <td class="total-revenue"></td>
            <td class="toner-coverage"></td>
            <td class="service-cpp"></td>
            <td class="total-cpp-cost"></td>
            <td class="supply-cost"></td>
            <td class="service-cost"></td>
            <td class="monthly-cost"></td>
            <td class="gp1"></td>
            <td class="gp2"></td></tr>`);
        update_costs_in_row(row, service, item.color_tier);
        footerCalculate(item.color_tier, update_row_in_summary_table);
    }
}


function calculate_gp_percentage(gp_total, total_revenue) {
    return gp_total / total_revenue;
}

function calculate_gp(total_revenue, monthly_cost) {
    return total_revenue - monthly_cost;
}

function calculate_monthly_cost(supply_cost, service_cost) {
    return supply_cost + service_cost;
}

function calculate_supply_cost(toner_coverage_55, total_volume) {
    return toner_coverage_55 * total_volume;
}

function calculate_total_cpp_cost(service_cpp, toner_coverage_55) {
    return service_cpp + toner_coverage_55;
}

function calculate_overage_cpp(overage_volume, base_rate, supply_cost, service_cost) {
    let targetMargin = 1 - (mgmtAsmpts.target_margin_toner + mgmtAsmpts.target_margin_service) / 2;
    let overage_cpp = (((supply_cost + service_cost) / targetMargin) - base_rate) / overage_volume;
    return isFinite(overage_cpp) ? overage_cpp : 0;
}

function calculate_overage_volume(total_volume, base_volume) {
    return total_volume - base_volume;
}

function calculate_service_cpp(service) {
    return service.service_cost / (service.total_mono_pages + service.total_color_pages) * (1 - mgmtAsmpts.target_margin_service);
}

function calculate_total_revenue_excel(revenue_cpp, overage_volume, base_rate) {
    return (revenue_cpp * overage_volume) + base_rate;
}

function nan_to_zero(item) {
    return isNaN(item) ? 0 : item;
}

function format_percentage(item) {
    let non_nan_item = nan_to_zero(item);
    return (non_nan_item * 100).toFixed(2) + '%';
}

function format_volume(item) {
    let non_nan_item = nan_to_zero(item);
    return non_nan_item.toFixed(0);
}

function format_cpp(item) {
    let non_nan_item = nan_to_zero(item);
    return '$' + non_nan_item.toFixed(4);
}

function format_cost(item) {
    let non_nan_item = nan_to_zero(item);
    return '$' + non_nan_item.toFixed(2);
}