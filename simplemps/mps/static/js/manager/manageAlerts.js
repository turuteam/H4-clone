$(document).ready(function() {
    $('#sfRequests').DataTable();
    $('#sfRequests_wrapper')
        .find('div.row.grid-x')
        .find('.small-6.columns.cell')
        .toggleClass('small-6 small-12')
        .css({
            'color': 'white'
        });

    $('#marginAlerts').DataTable();
    $('#marginAlerts_wrapper')
        .find('div.row.grid-x')
        .find('.small-6.columns.cell')
        .toggleClass('small-6 small-12')
        .css({
            'color': 'white'
        });
});

// eslint-disable-next-line no-unused-vars
function openStreetFighterReq(alertId) {
    getStreetFighterItems(alertId);
    $('#streetFighterReveal').foundation('open');
}

function getStreetFighterItems(alertId) {
    $.ajax({
        type: 'GET',
        cache: false,
        url: window.location.origin + '/alerts/getStreetFighterItems/' + alertId
    }).done(function (response) {
        $('#sfRevealBody').html(response.items);

        let totalCost = 0;
        $.each($('input[data-input="currentCost"]'), function (index, input) {
            totalCost += parseFloat(input.value);
        });

        $('#totalCost').val(totalCost.toFixed(2));
    }).fail(function (response) {
        alert(response.responseText);
    });
}

// eslint-disable-next-line no-unused-vars
function saveStreetFighterItems(alertId) {
    let rows = $('div[data-row-id]');
    let items = [];

    $.each(rows, function(index, row) {
        let reqCost = $(row).find('[data-input=reqCost]').val();
        let newCost = $(row).find('[data-input=newCost]').val();
        let item = {
            'part_type': $(row).data('part-type'),
            'part_id':  $(row).data('row-id'),
            'requested_price': reqCost !== '' ? reqCost : null,
            'new_price': newCost !== '' ? newCost : null
        };
        items.push(item) ;
    });

    $.ajax({
        type: 'POST',
        cache: false,
        url: window.location.origin + '/alerts/saveStreetFighterCosts/' + alertId + '/',
        data: {
            'items': JSON.stringify(items)
        }
    }).done(function(response) {
        if(response.status === 'Error') {
            alert(response.msg);
            return;
        }
        $('#streetFighterReveal').foundation('close');
    }).fail(function(response) {
        // do stuff, like, um, actually i don't know at the moment
    });
}

function acceptStreetFighterItems(proposal_id, alert_id) {
    $.ajax({
        type: 'POST',
        cache: false,
        url: window.location.origin + '/alerts/acceptStreetFighterPricing/' + proposal_id + '/',
    }).done(function(response) {
        saveStreetFighterItems(alert_id)
        $('#alert-' + alert_id).remove();
        $('#streetFighterReveal').foundation('close');
    })
}

function declineStreetFighterItems(proposal_id, alert_id) {
    $.ajax({
        type: 'POST',
        cache: false,
        url: window.location.origin + '/alerts/declineStreetFighterPricing/' + proposal_id + '/',
    }).done(function(response) {
        $('#alert-' + alert_id).remove();
        $('#streetFighterReveal').foundation('close');
    })
}

function downloadRequestedCosts() {
    let items = [['Product Number', 'Description', 'Current Cost', 'Requested Cost']];  //headers

    let rows = $('div[data-row-id]');
    $.each(rows, function(index, row) {
        let partId = $(row).data('row-id');
        let desc = $(row).find('[data-desc]').html();
        let curCost = $(row).find('[data-input=currentCost]').val();
        let reqCost = $(row).find('[data-input=reqCost]').val();
        items.push([partId, desc, curCost, reqCost]);
    });

    // Construct the comma seperated string
    const csv = items.map(function(row) {
        let str = '';
        for(let i = 0; i < row.length; i++) {
            if (i != row.length - 1) {
                str += row[i] + ',';
            } else {
                str += row[i] + '\n';
            }
        }
        return str;
    }).join('');

    // Format the CSV string
    const data = encodeURI('data:text/csv;charset=utf-8,' + csv);

    // Create a virtual Anchor tag
    const link = document.createElement('a');
    link.setAttribute('href', data);
    link.setAttribute('download', 'street_fighter_request.csv');

    // Append the Anchor tag in the actual web page or application
    document.body.appendChild(link);

    // Trigger the click event of the Anchor link
    link.click();

    // Remove the Anchor link from the page
    document.body.removeChild(link);
}

function approveMarginAlert(alertId, repId) {
    updateMarginAlert(alertId, repId, true);
    removeMarginAlertFromTable(alertId);
}

function denyMarginAlert(alertId, repId) {
    updateMarginAlert(alertId, repId, false); 
    removeMarginAlertFromTable(alertId);
}

function updateMarginAlert(alertId, repId, wasApproved) {
    $.ajax({
        method: 'PATCH',
        url: '/api/manager-alerts/' + alertId + '/',
        data: {
          'resolve_date': now(),
          'resolved_by': repId,
          'was_approved': wasApproved
        },
        context: $(this),
        success: function(data, status, jqXHR) {
            // do nothing for now
        },
    });
}

function removeMarginAlertFromTable(alertId) {
    const rowId = '#alert-' + alertId;
    $('#marginAlerts').DataTable().row(rowId).remove().draw();
}

function now() {
    var today = new Date();
    var dd = today.getDate();
    var mm = today.getMonth() + 1; // January is 0!
    var yyyy = today.getFullYear();
    if (dd < 10) {
        dd = '0' + dd;
    } 
    if (mm < 10) {
        mm = '0' + mm;
    } 
    return yyyy + '-' + mm + '-' + dd;
}