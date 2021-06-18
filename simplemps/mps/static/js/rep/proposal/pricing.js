'use strict';
/*global monoMargin*/
/*global monoColorMargin*/
/*global colorMargin*/
/*global minNetMargin*/

// hide tiered pricing until management assumptions are available (GEL 2019-08-31)
$('#tiered-button').hide();

// toggle TCO tab on/off based on management assumptions (GEL 2019-11-07)
/*if (mgmtAsmpts.allow_tco) {
    $('#tco-button2').show();
} else {
    $('#tco-button2').hide();
}; */
$('#tco-button3').hide();

$('#proposal-header-link').on('click', function() {
    saveBlendedProposalData();
    saveTieredProposalData();
    saveMarginData();
});

$('.btn-continue').on('click', function () {
    saveBlendedProposalData();
    saveTieredProposalData();
    saveMarginData();
    window.location.href = window.location.origin + '/proposal/preview/' + proposal_id;
});

function saveBlendedProposalData() {
    var bln_base_volume_mono = $('#total-mono-base-volume').html().replace(",", "");
    var bln_base_rate_mono = $('#total-mono-base-rate').html().replace("$", "");
    var bln_rcmd_price_mono = $('#monoBlended').html().replace("$", "");
    var bln_proposed_price_mono = $('#monoCPP').val();

    var bln_base_volume_mono_on_color = $('#total-mono-on-color-base-volume').html().replace(",", "");
    var bln_base_rate_mono_on_color = $('#total-mono-on-color-base-rate').html().replace("$", "");
    var bln_rcmd_price_mono_on_color = $('#monoColorBlended').html().replace("$", "");
    var bln_proposed_price_mono_on_color = $('#monoColorCPP').val();

    var bln_base_volume_color = $('#total-color-base-volume').html().replace(",", "");
    var bln_base_rate_color = $('#total-color-base-rate').html().replace("$", "");
    var bln_rcmd_price_color = $('#colorBlended').html().replace("$", "");
    var bln_proposed_price_color = $('#colorCPP').val();

    let blended_proposal_data = {
        'bln_base_volume_mono': bln_base_volume_mono,
        'bln_base_rate_mono': bln_base_rate_mono,
        'bln_rcmd_price_mono': bln_rcmd_price_mono,
        'bln_proposed_price_mono': bln_proposed_price_mono,
        'bln_base_volume_mono_on_color': bln_base_volume_mono_on_color,
        'bln_base_rate_mono_on_color': bln_base_rate_mono_on_color,
        'bln_rcmd_price_mono_on_color': bln_rcmd_price_mono_on_color,
        'bln_proposed_price_mono_on_color': bln_proposed_price_mono_on_color,
        'bln_base_volume_color': bln_base_volume_color,
        'bln_base_rate_color': bln_base_rate_color,
        'bln_rcmd_price_color': bln_rcmd_price_color,
        'bln_proposed_price_color': bln_proposed_price_color
    }

    $.ajax({
        type: 'POST',
        cache: false,
        data: {
            blended_proposal_data: JSON.stringify(blended_proposal_data),
        },
        url: window.location.origin + '/proposal/saveBlendedProposalData/' + proposal_id + '/'
    }).done(function (response) {
        // do nothing, for now
    }).fail(function () {
        alert('failed to save blended data');
    });
}

function saveTieredProposalData() {
    var bw1_overage_cpp = $('#bw1_overage_cpp').html().replace("$", "");
    var bw2_overage_cpp = $('#bw2_overage_cpp').html().replace("$", "");
    var bw3_overage_cpp = $('#bw3_overage_cpp').html().replace("$", "");
    var bw4_overage_cpp = $('#bw4_overage_cpp').html().replace("$", "");
    var color1_overage_cpp = $('#color1_overage_cpp').html().replace("$", "");
    var color2_overage_cpp = $('#color2_overage_cpp').html().replace("$", "");
    var color3_overage_cpp = $('#color3_overage_cpp').html().replace("$", "");

    let tiered_proposal_data = {
        'bw1_overage_cpp': bw1_overage_cpp,
        'bw2_overage_cpp': bw2_overage_cpp,
        'bw3_overage_cpp': bw3_overage_cpp,
        'bw4_overage_cpp': bw4_overage_cpp,
        'color1_overage_cpp': color1_overage_cpp,
        'color2_overage_cpp': color2_overage_cpp,
        'color3_overage_cpp': color3_overage_cpp
    }

    $.ajax({
        type: 'POST',
        cache: false,
        data: {
            tiered_proposal_data: JSON.stringify(tiered_proposal_data),
        },
        url: window.location.origin + '/proposal/saveTieredProposalData/' + proposal_id + '/'
    }).done(function (response) {
        // do nothing, for now
    }).fail(function () {
        alert('failed to save blended data');
    });
}

function saveMarginData() {
    localStorage.setItem('monoMargin', monoMargin);
    localStorage.setItem('monoColorMargin', monoColorMargin);
    localStorage.setItem('colorMargin', colorMargin);
    localStorage.setItem('minNetMargin', minNetMargin);
}
