$(document).ready(function() {
    if ($('#proposal-in-progress .clickable-row').length) { createDataTable('proposal-in-progress'); }
    if ($('#sent-proposals .clickable-row').length) { createDataTable('sent-proposals'); }
    if ($('#open-contracts .clickable-row').length) { createDataTable('open-contracts'); }
});

function createDataTable(selector){
    $('#' + selector).DataTable({
        searching: false,
        language: {
            paginate: {
                previous: '',
                next: ''
            }
        },
    });

    $('#' + selector + '_length').remove();
    $('#' + selector + '_wrapper')
        .find('div.row.grid-x')
        .find('.small-6.columns.cell')
        .toggleClass('small-6 small-12')
        .css({
            'color': 'white'
        })
}

$(document).on('click', '#proposal-in-progress>tbody>tr>.clickable-row', function(){
    proposalId = $(this).data('proposal-id');
    location.assign('/proposal/selectClient/' + proposalId);
});
$(document).on('click', '#sent-proposals>tbody>tr>.clickable-row', function(){
    proposalId = $(this).data('proposal-id');
    location.assign('/proposal/selectClient/' + proposalId);
});
$(document).on('click', '#open-contracts>tbody>.clickable-row', function(){
    proposalId = $(this).data('proposal-id');
    location.assign('/contract/view/' + proposalId);
});
$(document).on('click', '#addProposal', function(){
    $.ajax({
        type: 'POST',
        cache: false,
        url: window.location.origin + '/proposal/createNewProposal/',
        error: function(xhr, status, e) {
            alert(xhr + ' ' + status + ' ' + e);
        },
    }).done(function(response) {
        console.log('New Proposal Created!');
        window.location.href = '/proposal/selectClient/' + response.proposal_id;
    });
});

var items = {};
$(document).on('change', '.ChangeProposalStatus', function (el) {
    if(items[$(el.target).attr("proposal_id")]){
        var item = items[$(el.target).attr("proposal_id")];
        item.prev_status = item.status;
        item.status = $(el.target).val();
    }else{
        var item = {
            proposal_id: $(el.target).attr("proposal_id"),
            prev_status: $(el.target).attr("status"),
            status: $(el.target).val(),
            date_edited: $(el.target).attr("date_edited"),
            client: $(el.target).attr("client"),
        }
    }
    items[item.proposal_id] = item;
    $(el.target.parentNode.parentNode).remove();
    $('#'+item.status).append(`<tr class="row">
        <td class="clickable-row">"`+item.client+`"</td>
        <td>"`+item.date_edited+`"</td>
        <td>
            <select class="ChangeProposalStatus reduced_select" proposal_id="`+item.proposal_id+`" proposal-id="`+item.proposal_id+`" status="`+item.status+`" client="`+item.client+`" date_edited="`+item.date_edited+`">
                <option`+(item.status=='in-progress'&&' selected'||'')+` value="in-progress">in-progress</option>
                <option`+(item.status=='proposal_sent'&&' selected'||'')+` value="proposal_sent">sent</option>
                <option`+(item.status=='proposal_accepted'&&' selected'||'')+` value="proposal_accepted">accepted</option>
            </select>
        </td>
    </tr>`);
    $.ajax({
        type: 'POST',
        cache: false,
        data: {
            'proposal_data': JSON.stringify({
                status: item.status
            }),
            'proposal_id': item.proposal_id
        },
        url: window.location.origin + '/proposal/details/saveProposal/',
    }).done(function (response) {
        alert('Proposal Status updated!');
    });
    var prev_counter = $("#"+item.prev_status).attr('counter');
    $("#"+item.prev_status).attr('counter', --prev_counter);
    if(!Number(prev_counter)){
        console.log("#"+item.prev_status+'_counter', 'show on prev', $("#"+item.prev_status+'_counter'));
        $("#"+item.prev_status+'_counter').show();
    }
    $("#"+item.prev_status+'_counter_remove').hide();
    var counter = $("#"+item.status).attr('counter');
    $("#"+item.status).attr('counter', ++counter);
    if(Number(counter)){
        console.log("#"+item.status, 'hide on now');
        $("#"+item.status+'_counter').hide();
    }
    $("#"+item.status+'_counter_remove').hide();
});