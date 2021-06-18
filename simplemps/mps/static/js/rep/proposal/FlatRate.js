'use strict';
/* global p_objects */
/* global mgmtAsmpts */
/* global proposal_id */
/* global addThousandsSeparator */
/* global stripSpecialChars */
let FlatRaceTable;

$(document).ready(function () {
    // load the data from `proposal_service_items`
  // Add event listener to save changed values

  FlatRaceTable = $('#flat-rate-table').DataTable({
    'searching': false,
    'paging': false,
  });

  $(proposal_service_items).each(function() {
    appendFlatRaceTable($(this)[0]);
  });
});

function formatPrice() {
    return;
}

function calculateCostPerCartridgeMono() {
    return;
}

function calculateCostPerCartridgeColor() {
    return;
}

function appendFlatRaceTable(item) {
  FlatRaceTable.row.add([
    item.device_name,
    item.device_count,
    item.monthly_cost,
  ]).draw().nodes().to$().addClass('id-'+ item.id);
}