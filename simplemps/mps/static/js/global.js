$(document).foundation();

$(document).ready(function() {
    let p = window.location.pathname;

    if(p.indexOf('Dashboard') > 0) {
        $('#dash').addClass('is-active');
    } else if(p.indexOf('open') > 0) {
        $('#open').addClass('is-active');
    } else if(p.indexOf('sent') > 0) {
        $('#sent').addClass('is-active');
    } else if(p.indexOf('contracts') > 0) {
        $('#contracts').addClass('is-active');
    } else if(p.indexOf('SalesRep') > 0) {
        $('#sales_rep').addClass('is-active');
    } else if(p.indexOf('reps') > 0) {
        $('#reps').addClass('is-active');
    } else if(p.indexOf('Assumptions') > 0) {
        $('#assmpts').addClass('is-active');
    } else if(p.indexOf('alerts') > 0) {
        $('#alerts').addClass('is-active');
    } else if(p.indexOf('proposal') > 0) {
        $('#open').addClass('is-active');
    } else {
        $('#dash').addClass('is-active');
    }
});

function addThousandsSeparator(number) {
    let parts = number.toString().split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return parts.join('.');
}

function isNullOrWhitespace(input) {
    return !input || !input.trim();
}

function stripSpecialChars(value) {
    value = value.replace('$', '');
    value = value.replace('%', '');
    value = value.replace(',', '');
    return value;
}