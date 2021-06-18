$(document).ready(function () {
    // toggle TCO tab on/off based on management assumptions (GEL 2019-11-07)
    /*if (mgmtAsmpts.allow_tco) {
        $('#tco-button2').show();
    } else {
        $('#tco-button2').hide();
    }; */
    $('#tco-button1').hide();
});

function clearClientInfo() {
    $('#clientContactName').val('');
    $('#clientPhoneNumber').val('');
    $('#clientEmail').val('');
}

function clearEditInputs() {
    $('#editCompanyName').val('');
    $('#editContactName').val('');
    $('#editEmail').val('');
    $('#editNumber').val('');
    $('#editCity').val('');
    $('#editZip').val('');
    $('#editCountry').val('');
    $('#editAddress').val('');
    $('#editState').val('');
}

$('#clientSelect').on('change', function () {
    loadExistingClientInfo(this.value);
});

$('.edit-client-button').on('click', function () {
    var c_id = $('#clientSelect').val();
    if (c_id === '-1') {
        clearEditInputs();
    } else {
        var c_info = all_clients_info[c_id];
        $('#editCompanyName').val(c_info.organization_name);
        $('#editContactName').val(c_info.contact);
        $('#editEmail').val(c_info.email);
        $('#editNumber').val(c_info.phone_number);
        $('#editCity').val(c_info.city);
        $('#editZip').val(c_info.zipcode);
        $('#editCountry').val(c_info.country);
        $('#editAddress').val(c_info.address);
        $('#editState').val(c_info.state);
    }
});

$('.save-button').on('click', function () {
    saveProposal('save');
});

$('.continue-button').on('click', function () {
    saveProposal('continue');
});

$('#cancel-save-new-client').on('click', function () {
    // clear input boxes
});

$('#save-new-client').on('click', function () {
    // validation skipped, need implementation
    createNewClient();
});

$('#cancel-edit-client-info').on('click', function () {
    // clear user input changes
});

$('#save-edit-client-info').on('click', function () {
    c_id = $('#clientSelect').val();
    client = {
        'organization_name': $('#editCompanyName').val(),
        'contact': $('#editContactName').val(),
        'email': $('#editEmail').val(),
        'phone_number': $('#editNumber').val(),
        'address': $('#editAddress').val(),
        'city': $('#editCity').val(),
        'state': $('#editState').val(),
        'zipcode': $('#editZip').val(),
        'country': $('#editCountry').val(),
    }

    $.ajax({
        method: "POST",
        url: window.location.origin + '/proposal/selectClient/' + c_id + '/edit',
        data: {
            'client': JSON.stringify(client),
            'csrfmiddlewaretoken': $("input[name=csrfmiddlewaretoken]").val(),
        },
        success: function (response) {
            Object.assign(all_clients_info[c_id], client);
            $('#clientSelect option[value=' + c_id + ']').text(client.organization_name);
            loadExistingClientInfo(c_id);
            $('#editClient').foundation('close');
        },
        error: function (xhr, status, e, data) {
            alert(xhr + " " + status + " " + e);
        }
    });
})

function saveProposal(btn) {
    let data = {
        'proposal_id': proposal_id,
        'client_id': $('#clientSelect').val()
    }

    $.ajax({
        type: "POST",
        cache: false,
        data: {
            'data': JSON.stringify(data)
        },
        url: window.location.origin + "/proposal/selectClient/saveProposal/",
        error: function (xhr, status, e) {
            alert(xhr + " " + status + " " + e);
        }
    }).done(function (response) {
        if (btn == 'save') {
            window.location.href = '/repDashboard/';
        } else if (btn == 'continue') {
            window.location.href = '/proposal/details/' + proposal_id;
        }
    });
}

function createNewClient() {
    let companyName = $('#companyName').val();
    let contactName = $('#contactName').val();
    let email = $('#email').val();
    let phoneNumber = $('#new-number').val();
    let address = $('#address').val();
    let city = $('#city').val();
    let state = $('#state').val();
    let zip = $('#zip').val();
    let country = $('#country').val();

    client_info = {
        'organization_name': companyName,
        'contact': contactName,
        'email': email,
        'phone_number': phoneNumber,
        'address': address,
        'city': city,
        'state': state,
        'zipcode': zip,
        'country': country
    };
    $.ajax({
        type: "POST",
        cache: false,
        data: {
            'new_client_data': JSON.stringify(client_info)
        },
        url: window.location.origin + "/proposal/saveNewClient/"
    }).done(function (response) {
        alert("New Client saved!");
        $('#clientSelect').append($('<option>', {
            value: response.client_id,
            text: companyName
        }));
        $('#addClient').foundation('close');
    }).fail(function (xhr, status, e) {
        alert(xhr + " " + status + " " + e);
    });
}

function loadExistingClientInfo(client_id) {
    if (client_id === "-1") {        
        $('.edit-client-button').prop('disabled', true);
        clearClientInfo()
        return;
    }

    let client = all_clients_info[client_id];
    try {
        $('.edit-client-button').prop('disabled', false);
        $('#clientContactName').val(client.contact);
        $('#clientPhoneNumber').val(client.phone_number);
        $('#clientEmail').val(client.email);
    } catch (err) {
        console.log(client_id, client, all_clients_info);
    }
}