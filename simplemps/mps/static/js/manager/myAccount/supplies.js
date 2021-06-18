$(document).ready(function() {
    $('#suppliesTable').DataTable({
        ordering: false,
        searching: false,
        lengthChange: false
    });

    var wrapper = $('#suppliesTable_wrapper');
    wrapper.addClass('grid-x cell');
    wrapper = wrapper.find('div.row.grid-x');
    wrapper.addClass('cell');
    wrapper.find('.small-6.columns.cell').toggleClass('small-6 small-12');
});