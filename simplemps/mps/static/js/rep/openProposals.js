$(document).ready(function() {
    $('.delete').each(function(index, element) {
        $(element).on('click', function() {
            deleteProposal(this);
        });
    });
    
    $('.edit').each(function(index, element) {
        $(element).on('click', function() {
            editProposal(this);
        });
    });

    $('#add-proposal').on('click', function(){
            addProposal();
    });

    $("#open-proposals").DataTable();
    $('#open-proposals_wrapper')
    .find('div.row.grid-x')
    .find('.small-6.columns.cell')
    .toggleClass('small-6 small-12')
    .css({
        'color': 'white'
    });
});



function editProposal(row) {
    console.log('edit was clicked, still need to be implemented');
}

function editProposal(sender){
        window.location.href = '/proposal/selectClient/' + $(sender).attr('id').replace('e','')
}

function deleteProposal(sender) {
    let parentRow = $(sender).closest('tr');
    let proposal_id = $(sender).attr('id').replace('d','');

    request = $.ajax('removeProposal/', {
        type: 'POST',
        data: { id: proposal_id },
        success: function(data, status, jqXhr) {
            parentRow.remove();
        },
        error: function(jqXhr, textStatus, errorMessage) {
            alert('Some Error Happened');
        },
    });
}

function addProposal() {
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
}
