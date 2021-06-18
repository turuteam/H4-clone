// margin variables
var monoMargin = 0;
var monoColorMargin = 0;
var colorMargin = 0;
var minNetMargin = 0;

var proposal_id = window.location.pathname.split('/')[3];

$(document).ready(function(){
    $('.cell.button.mps-blue').click(function() {
        window.location.href= window.location.origin +'/proposal/pricing/' + proposal_id;
    });
    loadDetailOptions(proposal_details);
     
    // toggle TCO tab on/off based on management assumptions (GEL 2019-11-07)
    /*if (mgmtAsmpts.allow_tco) {
        $('#tco-button2').show();
    } else {
        $('#tco-button2').hide();
    }; */
    $('#tco-button5').hide();

    $('#previous-page').on('click', function(){
        window.location.href = window.location.origin + '/proposal/pricing/'+ proposal_id;
    });

    $('#save-proposal').on('click',function(){
        saveProposalType();
        window.location.href = window.location.origin + '/openProposals/';
    });

    retreiveMarginData();
});

$('#send-proposal').on('click', function() {
    saveProposalType();

    let netMargin = (monoMargin + monoColorMargin + colorMargin) / 3;

    if (netMargin < minNetMargin && !manangerApproval()) {
        alert("Margins are too low.\nPlease adjust pricing or wait for manager approval.");
        sendMarginAlert();
    } else {
        window.location.href = window.location.origin + '/proposal/send/' + proposal_id;
    }
});

$('#send-proposal-to-me').on('click', function() {
    saveProposalType();

    let netMargin = (monoMargin + monoColorMargin + colorMargin) / 3;

    if (netMargin < minNetMargin && !manangerApproval()) {
        alert("Margins are too low.\nPlease adjust pricing or wait for manager approval.");
        sendMarginAlert();
    } else {
        window.location.href = window.location.origin + '/proposal/send_to_me/' + proposal_id;
    }
});

$('#proposal-type').on('change', function() {
    var proposalType = $('#proposal-type').val();
    switch (proposalType) {
        case 'tiered':
            $('#embedded-proposal').attr('src', window.location.origin + '/proposal/view/tiered/' + proposal_id);
            break;
        case 'blended':
            $('#embedded-proposal').attr('src', window.location.origin + '/proposal/view/blended/' + proposal_id);
            break;
        case 'cpp':
            $('#embedded-proposal').attr('src', window.location.origin + '/proposal/view/cpp/' + proposal_id);
            break;
        case 'nc':
            $('#embedded-proposal').attr('src', window.location.origin + '/proposal/view/nc/' + proposal_id);
            break;
        case 'ppc':
            $('#embedded-proposal').attr('src', window.location.origin + '/proposal/view/ppc/' + proposal_id);
            break;
        default:
            alert("Choose a correct proposal type.");
    }
    saveProposalType();
});

$('#print-proposal').on('click', function() {
    var proposalType = $('#proposal-type').val();
    window.open(window.location.origin + '/proposal/view/' + proposalType + '/' + proposal_id + '/', '_blank');
})

function loadDetailOptions(details) {
    if (details.proposal_contractType != -1) {
        $('#contractTypeSelect option[value="' + (details.proposal_contractType) + '"]').prop('selected', true);
    }
    if (details.proposal_manufacturer != -1) {
        $('#manufacturerSelect option[value="' + details.proposal_manufacturer + '"]').prop('selected', true);
    }
}

function retreiveMarginData() {
    monoMargin = parseFloat(localStorage.getItem('monoMargin'));
    monoColorMargin = parseFloat(localStorage.getItem('monoColorMargin'));
    colorMargin = parseFloat(localStorage.getItem('colorMargin'));
    minNetMargin = parseFloat(localStorage.getItem('minNetMargin'));
}

function sendMarginAlert() {
    var data = [];

    // check to see if there is already a margin alert for this proposal
    getMarginAlert().done(function (response) {
        data = response;
    });

    // if there is not a margin alert for this proposal, create one
    if (data == undefined || data.length == 0) {
        let margin_alert_data = {
            alert_type: 'margin'
        }
    
        $.ajax({
            type: 'POST',
            cache: false,
            data: {
                margin_alert_data: JSON.stringify(margin_alert_data),
            },
            url: window.location.origin + '/proposal/saveMarginAlert/' + proposal_id + '/'
        }).done(function (response) {
            // do nothing, for now
        }).fail(function () {
            alert('failed to save margin alert data');
        });
    } else {
        alert('A margin alert has already been sent to your manager.');
    }
}

function manangerApproval() {
    var approval = false;
    var data = []

    getMarginAlert().done(function (response) {
        data = response;
    });

    if (data != undefined && data.length > 0) {
       approval = data[0].was_approved != null ? data[0].was_approved : false;
    }

    return approval;
}

function getMarginAlert() {
    return $.ajax({
        async: false,
        type: 'GET',
        url: window.location.origin + '/api/manager-alerts/?alert_type=margin&proposal_id=' + proposal_id
    });
}

function saveProposalType() {
    var proposalType = $('#proposal-type').val();

    $.ajax({
        type: 'PATCH',
        data: {
            'proposal_type': proposalType
        },
        url: window.location.origin + '/api/proposals/' + proposal_id + '/'
    });
}
