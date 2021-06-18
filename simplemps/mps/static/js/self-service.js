$(document).ready(function(){
    $('#id_recurring_client').change(function(){
        
        $.ajax({
            type: 'GET',
            cache: false,
            url: window.location.origin + '/api/client-info/' + $(this).val()
        }).done(function (response) {
            const client = response
            // fill out the form data
            $('#id_organization_name').val(client.organization_name);
            $('#id_contact').val(client.contact);
            $('#id_email').val(client.email);
            $('#id_phone_number').val(client.phone_number);
            $('#id_city').val(client.city);
            $('#id_state').val(client.state);
            $('#id_zipcode').val(client.zipcode);
            $('#id_country').val(client.country);
            // $('#id_rep_company').val(client.rep_company);
            
        }).fail(function (response) {
            alert(response.responseText);
        });
    });
    $('.self-service-save').click(function() {
            const step_proposal = document.getElementById('step-proposal');
            if(step_proposal.classList.contains('disabled')) {
                step_proposal.classList.remove('disabled');
                step_proposal.parentNode.classList.add('is-active');
                step_proposal.click();
            }
    })

    $('.self-service-next-page').click(function () {
        let url = window.location.toString();
        window.location.href = url.replace('equipment', 'selection');
    });

    $('.self-service-equipment').click(function () {
        let url = window.location.toString();
        window.location.href = url.replace('selection', 'equipment');
    });

    $('.self-service-proposal').click(function () {
        let url = window.location.toString();
        window.location.href = url.replace('selection', 'review');
    });
})
