$(document).ready(function() {
    $('#equipmentTable').DataTable({
        ordering: false,
        searching: false,
        lengthChange: false
    });

    var wrapper = $('#equipmentTable_wrapper');
    wrapper.addClass('grid-x cell');
    wrapper = wrapper.find('div.row.grid-x');
    wrapper.addClass('cell');
    wrapper.find('.small-6.columns.cell:first-child').toggleClass('small-6 small-12');
    wrapper.find('.small-6.columns.cell:last-child').toggleClass('small-6 small-11');
});