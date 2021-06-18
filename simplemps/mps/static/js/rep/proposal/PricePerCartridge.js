'use strict';
/* global p_objects */
/* global mgmtAsmpts */
/* global proposal_id */
/* global addThousandsSeparator */
/* global stripSpecialChars */
let costPerCartridgeTable;

$(document).ready(function () {
    // load the data from `proposal_service_items`
  // Add event listener to save changed values

  costPerCartridgeTable = $('#price-per-cartridge-table').DataTable({
    'searching': false,
    'paging': false,
  });

  $(proposal_service_items).each(function() {
    appendToCartridgeTable($(this)[0]);
  });
});


function patchProposalServiceItem() {
    const url = `/api/proposal-service-items/${this.dataset.id}/`;

    $.ajax({
      method: 'PATCH',
      url: url,
      headers: {
        "X-CSRFTOKEN": csrftoken
      },
      data: {
        proposed_cost_per_cartridge_mono: $(`#${this.dataset.id}-proposed-cpc-mono`).val(),
        proposed_cost_per_cartridge_color: $(`#${this.dataset.id}-proposed-cpc-color`).val(),
      },
      context: $(this),
      success: function(response, status, jqXHR) {
        console.log(response, status);
      },
    });
}

function formatPrice() {
    return;
}

function calculateCostPerCartridgeMono() {
    return;
}

function calculateCostPerCartridgeColor() {
    return;
}

function appendToCartridgeTable(item) {
  costPerCartridgeTable.row.add([
    item.short_model,
    item.recommended_cost_per_cartridge_mono,
    item.recommended_cost_per_cartridge_color,
    `<input type=number id="${item.id}-proposed-cpc-mono" value=${item.proposed_cost_per_cartridge_mono || 0.00} step=".0001" />`,
    `<input type=number id="${item.id}-proposed-cpc-color" value=${item.proposed_cost_per_cartridge_color || 0.00} step=".0001" />`,
    `<input class="button" type=button value="Save" data-id="${item.id}" onclick="patchProposalServiceItem.call(this)" />`
  ]).draw().nodes().to$().addClass('id-'+ item.id);
}