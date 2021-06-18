/*global p_objects*/
/*global mgmtAsmpts*/
/*global proposal_service_items*/
/*global proposal_purchase_items*/
/*global monoMargin*/
/*global monoColorMargin*/
/*global colorMargin*/
/*global minNetMargin*/
/*global addThousandsSeparator*/
/*global isNullOrWhitespace*/
/*global mps_price*/
/*global monthly_lease*/
/*global proposal_term*/


var proposal_id = window.location.pathname.split('/')[3];
var level = 4;

let tco_table;
let tco_devices = [];

let cache = {};

let page_cost_details;

let proposal_settings;
let network_devices = [];

let saveEquipment = false;

$(document).ready(function (){

    if (window.location.pathname.indexOf('/sync') >= 0) {
      window.location.pathname = window.location.pathname.replace('/sync', '');
    }

    proposal_settings = loadProposalSettings(mgmtAsmpts.proposal_id);
    deviceShortName = $('#tcoDevice-shortName').val();
    deviceMakeName = $('#tcoDevice-makeName').val();

    proposalTCO_data = loadProposalTCO(proposal_id);

    tco_table = $('#tco-devices-table').DataTable({
      'searching':false,
      'pageLength': 10,
      'lengthChange': false,
      'columnDefs': [{ 'orderable': false, 'targets': 11}]
    }); 

    $('#tco-devices-table').addClass('tco-table').addClass('size-14');

    $('#tco-devices-table_wrapper')
        .find('div.row.grid-x')
        .find('.small-6.columns.cell')
        .toggleClass('small-6 small-12')
        .addClass('data_table_wrapper')
        .css({
        'color': 'white'
    });

    $("#client-content2").show();

    loadTCOOptions(proposalTCO_data);

    [tco_table].forEach(table => {
        $(table.table().body()).on('click', 'tr td button[data-type="remove-device"]', function () {
            let row = $(this).parents('tr');
            const id = row.attr('id');
            row = table.row(row);
            $.ajax({
                type: 'POST',
                cache: false,
                data: { id: id },
                url: window.location.origin + '/proposal/removeTCODevice/' + proposal_id + '/'
            }).done(function () {
                row.remove().draw();
                $(`tr[data-id="${id}"]`).remove();
                updateCostSummary();
            }).fail(function () {
                alert('failed to remove TCO device');
            });
        });

        $(table.table().body()).on('click', 'tr td button[data-type="edit-device"]', function () {
          let row = $(this).parents('tr');
          const id = row.attr('id');

          $.ajax({
            type: 'GET',
            cache: false,
            data: { id: id },
            url: window.location.origin + '/proposal/TCODeviceDetails/' + proposal_id + '/'
          }).done(response => {
            const { 
              device: {
                id,
                number_printers_serviced,
                monthly_lease_payment,
                total_mono_pages,
                total_color_pages,
                base_volume_mono,
                base_volume_color,
                base_rate_mono,
                base_rate_color,
                rcmd_cpp_color,
                rcmd_cpp_mono
              }, 
              printer: { id: printer_id, display_description, is_color_device }
            } = response;
            $('#edit-tco-device').attr('printer-id', printer_id)
            $('#edit-tco-device').attr('device-id', id)
            $('#hide-total-color').css('display', '')
            $('#hide-volume-color').css('display', '')
            $('#hide-rate-color').css('display', '')
            $('#hide-cpp-color').css('display', '')

            $('#editTCODevice').foundation('open');
            $('#edit-tcoDevice-shortName').text(display_description)
            $('#edit-tcoDevice-quantity').val(number_printers_serviced)
            const monthly_lease = monthly_lease_payment ? monthly_lease_payment : 0;
            $('#edit-monthly-lease-payment').val(monthly_lease)
            $('#edit-total-monthly-mono-pages').val(total_mono_pages)
            $('#edit-total-monthly-color-pages').val(total_color_pages)
            $('#edit-base-volume-mono').val(base_volume_mono)
            $('#edit-base-volume-color').val(base_volume_color)
            $('#edit-base-rate-mono').val(base_rate_mono)
            $('#edit-base-rate-color').val(base_rate_color)
            $('#edit-current-mono-cpp').val(rcmd_cpp_mono)
            $('#edit-current-color-cpp').val(rcmd_cpp_color)

            if (!is_color_device) {
              $('#hide-total-color').css('display', 'none')
              $('#hide-volume-color').css('display', 'none')
              $('#hide-rate-color').css('display', 'none')
              $('#hide-cpp-color').css('display', 'none')
            }
          })
        });
    });

    updateSummaryAndMonthly();
    loadMakeDetails();

    // add event to detect change in Make then reload shortName dropdown
    $('#tcoDevice-makeName').on('change', function() {loadPrinterDetailsByMake()});
    $('#nontcoDevice-makeName').on('change', function() {loadPrinterDetailsByMakeNN()});

    loadPrinterDetails();

    $('#add-device-tco').on('click', function() {
      modal_mode = 'new';
      resetTCODeviceModal();
      $('#addTCODevice').foundation('open');
    });

    // update modal UI as data is entered/edited
    $('#addTCODevice .reactive').on('input', updateModalUI);

    updateCostSummary();
});

function loadProposalSettings(proposal_id) {
  var return_data;
  $.ajax({
      type: 'GET',
      async: false,
      cache: false,
      url: window.location.origin + '/proposal/getProposalSettings/' + proposal_id
  }).done(function (response) {
      return_data = JSON.parse(response);
  }).fail(function (error) {
      alert(error);
  });
  return return_data;
}

function updateModalUI() {
  const pageInfo = {
      monoMonthly: parseInt($('#total-monthly-mono-pages').val()) || 0,
      colorMonthly: parseInt($('#total-monthly-color-pages').val()) || 0,
      monoCoverage: parseFloat($('#mono-coverage').val()) || 0,
      colorCoverage: parseFloat($('#color-coverage').val()) || 0,
  }
  pageInfo.totalMonthly =  pageInfo.monoMonthly + pageInfo.colorMonthly;
  $('#total-monthly-pages').val(pageInfo.totalMonthly);

  const recommendedPrice = {
      monoToner: updateRecommendMonoTonerPrice(toner_costs.scaled_mono_cost, pageInfo.monoMonthly, pageInfo.monoCoverage),
      colorToner: updateRecommendColorTonerPrice(toner_costs.scaled_color_cost, pageInfo.colorMonthly, pageInfo.colorCoverage),
      service: updateRecommendServicePrice(toner_costs.scaled_service_cost, pageInfo.totalMonthly),
  };
  recommendedPrice.monoSales =  updateRecommendMonoSalesPrice(recommendedPrice.monoToner, recommendedPrice.service, pageInfo.monoMonthly, pageInfo.colorMonthly);
  recommendedPrice.colorSales = updateRecommendColorSalesPrice(recommendedPrice.colorToner, recommendedPrice.service, pageInfo.monoMonthly, pageInfo.colorMonthly);
  recommendedPrice.monthly = updateRecommendMonthlyPrice(recommendedPrice.monoToner, recommendedPrice.colorToner, recommendedPrice.service);

  const proposedPrice = {
      baseMonoVolume: parseInt($('#base-volume-mono').val()) || 0,
      baseColorVolume: parseInt($('#base-volume-color').val()) || 0,
      baseMonoRate: parseFloat($('#base-rate-mono').val()) || 0,
      baseColorRate: parseFloat($('#base-rate-color').val()) || 0,
      monoSalesPrice: parseFloat($('#current-mono-cpp').val()) || 0,
      colorSalesPrice: parseFloat($('#current-color-cpp').val()) || 0,
  };

  let device_type;
  const id = $('add-tco-device').data('id');

  if (id) {
      device_type = p_objects[id].service.device_type
  } else if (printer_details !== undefined) {
      device_type = printer_details.device_type;
  }

  // if margin locked, see if proposed pricing need to be adjusted  (gel 2019-11-25)
  // otherwise just save any possible changes in case switch is changed back
  if($('#lock-margin').val() == '1') {
      let changeType = "unknown";
      equalizeMargin(changeType);             
  } else {
      $('#saved-mono-sales').val($('#current-mono-cpp').val());
      $('#saved-color-sales').val($('#current-color-cpp').val());
  }
}

function updateRecommendMonoTonerPrice(scaledTonerCPP, pages, monoCoverage) {
  // service only = 0
  if (mgmtAsmpts.contract_service_type === 'service_only') {
      $('#recommended-mono-toner-price').html('0');
      return 0;
  }

  let monoTonerPrice = getRecommendMonoTonerPrice(scaledTonerCPP, pages, monoCoverage);
  $('#recommended-mono-toner-price').html(monoTonerPrice);
  return monoTonerPrice;
}

function getRecommendMonoTonerPrice(scaledTonerCPP, pages, monoCoverage) {
  // Pages * (CPP * Coverage / 0.05) / (1 - Toner Margin)
  return +(pages * (scaledTonerCPP * (monoCoverage / 0.05))).toFixed(4); // return float instead of string
}

function loadMakeDetails() {
  $.ajax({
      type: 'GET',
      cache: false,
      url: window.location.origin + '/proposal/getMakeDetails/'
  }).done(function (response) {
      let makes = JSON.parse(response).makes;
      appendMakeDetails($('#tcoDevice-makeName'), makes);
      appendMakeDetails($('#nontcoDevice-makeName'), makes);
  }).fail(function (error) {
      console.log(error);
  });
}

function appendMakeDetails(makeDropDown, makes) {
  makeDropDown.append($('<option>', { value: -1, text: '', hidden: true }));
  for (let i = 0; i < makes.length; i++) {
      let make = makes[i];
      makeDropDown.append($('<option>', { value: make[0], text: make[1] }));
  }
}

function loadPrinterDetails() {
  $.ajax({
      type: 'GET',
      cache: false,
      url: window.location.origin + '/proposal/getPrinterDetails/'
  }).done(function (response) {
      let printers = JSON.parse(response).printers;
      appendPrinterDetails($('#tcoDevice-shortName'), printers);
      appendPrinterDetails($('#nontcoDevice-shortName'), printers);
  }).fail(function (error) {
      console.log(error);
  });
}

function appendPrinterDetails(deviceDropDown, printers) {
  deviceDropDown.append($('<option>', { value: -1, text: '', hidden: true }));
  for (let i = 0; i < printers.length; i++) {
      let printer = printers[i];
      deviceDropDown.append($('<option>', { value: printer[0], text: printer[1] }));
  }
}

function loadProposalTCO(proposal_id) {
    var return_data;
    $.ajax({
        type: 'GET',
        async: false,
        cache: false,
        url: window.location.origin + '/proposal/getTCO/' + proposal_id
    }).done(function (response) {
        return_data = JSON.parse(response);
    }).fail(function (error) {
        alert(error);
    });
    return return_data;
}

function loadTCOOptions(details) {
    $('#currentContractTypeSelect option[value="' + (proposalTCO_data.contract_service_type) + '"]').prop('selected', true);
    $("#currentTotalSupplySpend").val(proposalTCO_data.total_supply_spend);
    $("#currentTotalServiceSpend").val(proposalTCO_data.total_service_spend);
    $("#currentTotalLeaseSpend").val(proposalTCO_data.total_lease_spend);
    $("#currentTransactionCost").val(proposalTCO_data.est_transaction_overhead);
    $("#currentSalesOrderCount").val(proposalTCO_data.total_sales_orders);
    $("#currentServiceOrderCount").val(proposalTCO_data.total_service_orders);
}

$('#previous-page').on('click', function(){
    saveProposalTCO('continue');
    //window.location.href = window.location.origin + '/proposal/selectClient/'+ parseInt(proposal_id);
});

$('#save-details').on('click', function() {
    saveProposalTCO('save');
});

$('#continue-details').on('click', function() {
    saveProposalTCO('continue');
});

function saveProposalTCO(btn) {
    proposalTCO_data = {
        'contract_service_type': $('#currentContractTypeSelect').val(),
        'total_supply_spend': parseFloat($('#currentTotalSupplySpend').val()),
        'total_service_spend': parseFloat($('#currentTotalServiceSpend').val()),
        'total_lease_spend': parseFloat($('#currentTotalLeaseSpend').val()),
        'est_transaction_overhead': parseFloat($('#currentTransactionCost').val()),
        'total_sales_orders': parseFloat($('#currentSalesOrderCount').val()),
        'total_service_orders':parseFloat($('#currentServiceOrderCount').val()),
        'proposal_id': proposal_id
    };

    $.ajax({
        type: 'POST',
        cache: false,
        data: {
            'proposalTCO_data': JSON.stringify(proposalTCO_data),
            'proposal_id': proposal_id
        },
        url: window.location.origin + '/proposal/TCO/saveProposalTCO/',
        error: function (xhr, status, e) {
            alert('function error');
            alert(xhr + ' ' + status + ' ' + e);
        }
    }).done (function(response) {
        if (btn == 'save') {
            window.location.href = '/repDashboard';
        } else if (btn == 'continue') {
            window.location.href = '/proposal/pricing/' + parseInt(proposal_id);
            //window.location.href = '/proposal/pricing/' + parseInt(response.proposal_id);
        } else {
            alert('Warning!!!');
        }
    });
}

$('#edit-tco-device').on('click', function () {
  const id = $('#edit-tco-device').attr('device-id')
  display_description = $('#edit-tcoDevice-shortName').text()
  number_printers_serviced = $('#edit-tcoDevice-quantity').val()
  monthly_lease_payment = $('#edit-monthly-lease-payment').val()
  total_mono_pages = $('#edit-total-monthly-mono-pages').val()
  total_color_pages = $('#edit-total-monthly-color-pages').val()
  base_volume_mono = $('#edit-base-volume-mono').val()
  base_volume_color = $('#edit-base-volume-color').val()
  base_rate_mono = $('#edit-base-rate-mono').val()
  base_rate_color = $('#edit-base-rate-color').val()
  rcmd_cpp_mono = $('#edit-current-mono-cpp').val()
  rcmd_cpp_color = $('#edit-current-color-cpp').val()

  device = {
    id,
    number_printers_serviced,
    monthly_lease_payment,
    total_mono_pages,
    total_color_pages,
    base_volume_mono,
    base_volume_color,
    base_rate_mono,
    base_rate_color,
    current_cpp_mono: rcmd_cpp_mono,
    current_cpp_color: rcmd_cpp_color
  }

  $.ajax({
    type: 'POST',
    cache: false,
    data: JSON.stringify({ device: device }),
    url: window.location.origin +`/proposal/TCO/${proposal_id}/updateTCODevice/`
  }).done(() => {
    window.location.pathname = `/proposal/TCO/${proposal_id}/`
  })
})


// to-do needs converted from network to tco
$('#add-tco-device').on('click', function () {
    // add new network device into table, keys in the object match those in the database (besides equipment which needs to be added eventually!)
    let id = $(this).data('id');


    // if there is an id, we are editing an existing tco item, i think. maybe, maybe not. we'll see
    if (id) {
        let url = '/api/proposal-tco-items/' + id + '/'

        let selector = `#tco-devices-table tr[data-id="${id}"]`;

        const row = tco_table.row(selector);
        let data = row.data();

        $.ajax({
            method: 'PATCH',
            url: url,
            headers: {
              "X-CSRFTOKEN": csrftoken
            },
            data: {
              number_printers_serviced: $('#tcoDevice-quantity').val() || 1,
              total_mono_pages: parseInt($('#total-monthly-mono-pages').val()) || 0,
              total_color_pages: parseInt($('#total-monthly-color-pages').val()) || 0,

              monthly_lease_payment: $('#monthly-lease-payment').val() || 0,

              current_cpp_mono: $('#current-mono-sales').val(),
              current_cpp_color: $('#current-color-sales').val(),

              rcmd_cpp_mono: $('#recommended-mono-sales-price').text(),
              rcmd_cpp_color: $('#recommended-color-sales-price').text(),

              base_volume_mono: parseInt($('#base-volume-mono').val()) || 0,
              base_rate_mono: $('#base-rate-mono').val() || 0,
              base_volume_color: parseInt($('#base-volume-color').val()) || 0,
              base_rate_color: $('#base-rate-color').val() || 0
            },
            context: $(this),
            success: function(response, status, jqXHR) {
                data[1] = response.number_printers_serviced;
                data[2] = response.total_mono_pages;
                data[3] = response.total_color_pages;
                data[4] = response.base_volume_mono || '---';
                data[5] = +response.base_rate_mono ? response.base_rate_mono : '---';
                data[6] = response.base_volume_color || '---';
                data[7] = +response.base_rate_color ? response.base_rate_color : '---';
                data[8] = +response.rcmd_cpp_mono ? Number.parseFloat(response.rcmd_cpp_mono).toFixed(4) : '---';
                data[9] = +response.rcmd_cpp_color ? Number.parseFloat(response.rcmd_cpp_color).toFixed(4) : '---';

                row.data(data).draw();

                location.reload(); // TODO Refreshing for now; recalculate tier and summary values without reload later
            },
        });
    } else {
        let short_model = $('#tcoDevice-shortName :selected').text();

        let proposed_network_service = {
            printer: parseInt($('#tcoDevice-shortName').val()),
            number_printers_serviced: parseInt($('#tcoDevice-quantity').val()),
            monthly_lease_payment: isNaN(parseFloat($('#monthly-lease-payment').val())) ? 0 : parseFloat($('#monthly-lease-payment').val()).toFixed(2),
            total_mono_pages: parseInt($('#total-monthly-mono-pages').val()) || 0,
            total_color_pages: parseInt($('#total-monthly-color-pages').val()) || 0,
            base_volume_mono: parseInt($('#base-volume-mono').val()) || 0,
            base_volume_color: parseInt($('#base-volume-color').val()) || 0,
            base_rate_mono: isNaN(parseFloat($('#base-rate-mono').val())) ? 0 : parseFloat($('#base-rate-mono').val()).toFixed(2),
            base_rate_color: isNaN(parseFloat($('#base-rate-color').val())) ? 0 :parseFloat($('#base-rate-color').val()).toFixed(2),
            current_cpp_mono: isNaN(parseFloat($('#current-mono-cpp').val())) ? 0 : parseFloat($('#current-mono-cpp').val()).toFixed(4),
            current_cpp_color: isNaN(parseFloat($('#current-color-cpp').val())) ? 0 : parseFloat($('#current-color-cpp').val()).toFixed(4),
            is_non_network: false
        };

        let buy_or_lease = '';
        let proposed_cost = 0;

        $.ajax({
            type: 'POST',
            cache: false,
            data: {
                proposed_service: JSON.stringify(proposed_network_service)
            },
            url: window.location.origin + '/proposal/addTCODevice/' + proposal_id + '/'
        }).done(function (response) {
            const { device: { id } } = response;
            proposed_network_service['short_model'] = short_model;
            proposed_network_service['is_color_device'] = printer_details.printer_is_color_type;
            proposed_network_service['id'] = id;
            proposed_network_service['buy_or_lease'] = buy_or_lease;
            proposed_network_service['proposed_cost'] = proposed_cost;

            appendToTCOTable(proposed_network_service);

        }).fail(function () {
            alert('failed to add TCO device');
        });
    }
})

function resetTCODeviceModal() {
  // reset the modal UI to the default/initial state
  $('#tcoDevice-shortName').val('');
  $('#tcoDevice-shortName').prop('disabled', false);
  $('#tcoDevice-quantity').val('1');
  $('#equipment-options').prop('disabled', true);
  $('#tcoDevice-totalOutcost').val('');
  $('#tcoDevice-totalOutcost').prop('disabled', true);
  $('#tcoDevice-purchasePrice').val('');
  $('#tcoDevice-purchasePrice').prop('disabled', true);
  $('#total-monthly-mono-pages').val('');
  $('#total-monthly-color-pages').val('');
  $('#total-monthly-pages').val('');
  $('#mono-coverage').val('.05');
  $('#color-coverage').val('.05');
  $('#color-coverage').prop('disabled', true);
  $('#recommended-mono-toner-price').html('0');
  $('#recommended-color-toner-price').html('0');
  $('#recommended-service-price').html('0');
  $('#recommended-monthly-price').html('0');
  $('#recommended-mono-sales-price').html('0.0000');
  $('#recommended-color-sales-price').html('0.0000');
  $('#bundled-monthly-mono-pages').val('');
  $('#bundled-monthly-color-pages').val('');
  $('#recommended-mono-sales-price2').val(0);
  $('#recommended-color-sales-price2').val(0);
  $('#bundled-mono-price').val(0);
  $('#bundled-color-price').val(0);
  $('#bundled-mono-monthly').val(0);
  $('#bundled-color-monthly').val(0);
  $('#bundledAmt').val(0);
  $('#base-volume-mono').val('');
  $('#base-volume-color').val('');
  $('#base-volume-color').prop('disabled', true);
  $('#base-rate-mono').val('');
  $('#base-rate-color').val('');
  $('#base-rate-color').prop('disabled', true);
  $('#current-mono-cpp').val('');
  $('#current-color-cpp').val('');
  $('#add-tco-device').prop('disabled', true);
  $('#add-tco-device').data('id', null);
  $('#add-tco-device').html('Save');
//    $('#monthly-payment').val(0);
  $('#buy-lease').val('buy');
}

function updateSummaryAndMonthly() {
  updateSummaryInfo();
  calculateMargin();
  updateMonthlyTotals();
  updateOverallMargin();
}

function updateSummaryInfo() {
  // $('.term').text(mgmtAsmpts.term);

  resetRunningTotals();

  let baseVolMono = 0;
  let baseVolMonoColor = 0;
  let baseVolColor = 0;
  let baseRateMono = 0;
  let baseRateMonoColor = 0;
  let baseRateColor = 0;
  let overMono = 0;
  let overMonoColor = 0;
  let overColor = 0;

  for (let i of Object.keys(p_objects)) {
      let device = p_objects[i].service;
      // only include network devices
      if (device.is_non_network) continue;

      let serviceCost = parseFloat(device.service_cost) * (1 - mgmtAsmpts.target_margin_service);
      let totalPages = device.total_mono_pages + device.total_color_pages;

      let rcmdMonoToner;
      let rcmdColorToner;
      let sf_mono_price;
      let sf_color_price;
      $.ajax({
          type: 'POST',
          cache: false,
          data: { 'device_id': device.printer_id, 'proposal_id': device.proposal_id },
          url: window.location.origin + '/proposal/getNetworkDeviceDetails/',
          async: false
      }).done(function (response) {
          toner_costs = response.toners_costs;
          rcmdMonoToner = getRecommendMonoTonerPrice(toner_costs.scaled_mono_cost, device.total_mono_pages, device.mono_coverage);
          rcmdColorToner = getRecommendColorTonerPrice(toner_costs.scaled_color_cost, device.total_color_pages, device.color_coverage);
          let rcmdService = getRecommendServicePrice(toner_costs.scaled_service_cost, totalPages);

          sf_mono_price = getRecommendMonoSalesPrice(rcmdMonoToner, rcmdService, device.total_mono_pages, device.total_color_pages);
          sf_color_price = getRecommendColorSalesPrice(rcmdColorToner, rcmdService, device.total_mono_pages, device.total_color_pages);
      });

      if (device.is_color_device) {
          //================= monocolor
          baseVolMonoColor += device.base_volume_mono;
          baseRateMonoColor += parseFloat(device.base_rate_mono);

          let overage = device.total_mono_pages - device.base_volume_mono;
          overMonoColor += overage > 0 ? overage : 0;

          let salesPrice;

          salesPrice = parseFloat(device.proposed_cpp_mono) > 0 ? parseFloat(device.proposed_cpp_mono) : parseFloat(device.rcmd_cpp_mono);
          runningMonoColorPrice += salesPrice * overage + parseFloat(device.base_rate_mono);

          let monoColorCost = parseFloat(device.mono_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
          runningMonoColorCost += totalPages === 0 ? 0 : monoColorCost + (serviceCost * device.total_mono_pages / totalPages);

          //================= color
          baseVolColor += device.base_volume_color;
          baseRateColor += parseFloat(device.base_rate_color);

          overage = device.total_color_pages - device.base_volume_color;
          overColor += overage > 0 ? overage : 0;

          if (streetFighter && sf_color_price) {
              device.rcmd_cpp_color = sf_color_price;
              device.color_toner_price = rcmdColorToner;
              let serviceItem = proposal_service_items.find(x => x.id === device.id);
              serviceItem.rcmd_cpp_color = sf_color_price;
              let row = tco_table.row('[data-id="'+ device.id +'"]');
              row.cell('td:nth-of-type(10)').data(sf_color_price).draw()
          }
          salesPrice = parseFloat(device.proposed_cpp_color) > 0 ? parseFloat(device.proposed_cpp_color) : parseFloat(device.rcmd_cpp_color);
          runningColorPrice += salesPrice * overage + parseFloat(device.base_rate_color);

          let colorCost = parseFloat(device.color_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
          runningColorCost += totalPages === 0 ? 0 : colorCost + (serviceCost * device.total_color_pages / totalPages);
      } else {
          //================= mono
          baseVolMono += device.base_volume_mono;
          baseRateMono += parseFloat(device.base_rate_mono);
          let overage = device.total_mono_pages - device.base_volume_mono;
          overMono += overage > 0 ? overage : 0;
          let salesPrice;
          if (streetFighter && sf_mono_price) {
              device.rcmd_cpp_mono = sf_mono_price;
              device.mono_toner_price = rcmdMonoToner;
              let serviceItem = proposal_service_items.find(x => x.id === device.id);
              serviceItem.rcmd_cpp_mono = sf_mono_price;
              let row = tco_table.row('[data-id="'+ device.id +'"]');
              row.cell('td:nth-of-type(9)').data(sf_mono_price).draw()
          }
          salesPrice = parseFloat(device.proposed_cpp_mono) > 0 ? parseFloat(device.proposed_cpp_mono) : parseFloat(device.rcmd_cpp_mono);
          runningMonoPrice += salesPrice * overage + parseFloat(device.base_rate_mono);
          let monoCost = parseFloat(device.mono_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
          runningMonoCost += totalPages === 0 ? 0 : monoCost + (serviceCost * device.total_mono_pages / totalPages);
      }
  }
  $('#total-mono-base-volume').text(addThousandsSeparator(baseVolMono));
  $('#total-mono-base-rate').text('$' + addThousandsSeparator(baseRateMono.toFixed(2)));
  $('#overage-mono-volume').text(addThousandsSeparator(overMono));
  $('#monoBlended').text(overMono != 0 ? '$' + ((runningMonoPrice - baseRateMono) / overMono).toFixed(4) : '$0');
  monoMargin = runningMonoPrice > 0 ? ((runningMonoPrice - runningMonoCost) / runningMonoPrice * 100).toFixed(0) : 0;
  $('#monoMargin').text(monoMargin + '%');
  if (monoMargin / 100 < mgmtAsmpts.min_mono_margin) {
      $('#monoMargin').addClass('warning');
  } else {
      $('#monoMargin').removeClass('warning');
  }

  $('#total-mono-on-color-base-volume').text(addThousandsSeparator(baseVolMonoColor));
  $('#total-mono-on-color-base-rate').text('$' + addThousandsSeparator(baseRateMonoColor.toFixed(2)));
  $('#overage-mono-on-color-volume').text(addThousandsSeparator(overMonoColor));
  $('#monoColorBlended').text(overMonoColor != 0 ? '$' + ((runningMonoColorPrice - baseRateMonoColor) / overMonoColor).toFixed(4) : '$0');
  monoColorMargin = runningMonoColorPrice > 0 ? ((runningMonoColorPrice - runningMonoColorCost) / runningMonoColorPrice * 100).toFixed(0) : 0;
  $('#monoColorMargin').text(monoColorMargin + '%');
  if (monoColorMargin / 100 < mgmtAsmpts.min_mono_on_color_margin) {
      $('#monoColorMargin').addClass('warning');
  } else {
      $('#monoColorMargin').removeClass('warning');
  }

  $('#total-color-base-volume').text(addThousandsSeparator(baseVolColor));
  $('#total-color-base-rate').text('$' + addThousandsSeparator(baseRateColor.toFixed(2)));
  $('#overage-color-volume').text(addThousandsSeparator(overColor));
  $('#colorBlended').text(overColor != 0 ? '$' + ((runningColorPrice - baseRateColor) / overColor).toFixed(4) : '$0');
  colorMargin = runningColorPrice > 0 ? ((runningColorPrice - runningColorCost) / runningColorPrice * 100).toFixed(0) : 0;
  $('#colorMargin').text(colorMargin + '%');
  if (colorMargin / 100 < mgmtAsmpts.min_color_margin) {
      $('#colorMargin').addClass('warning');
  } else {
      $('#colorMargin').removeClass('warning');
  }
}

function resetRunningTotals() {
  runningMonoPrice = 0;
  runningMonoColorPrice = 0;
  runningColorPrice = 0;
  runningMonoCost = 0;
  runningColorCost = 0;
  runningMonoColorCost = 0;
}

function updateRecommendColorTonerPrice(colorTonerMarginPrice, totalMonthlyColorPages, colorCoverage) {
  // if service only, return 0
  if (mgmtAsmpts.contract_service_type === 'service_only') {
      $('#recommended-color-toner-price').html('0');
      return 0;
  }

  let colorTonerPrice = getRecommendColorTonerPrice(colorTonerMarginPrice, totalMonthlyColorPages, colorCoverage);
  $('#recommended-color-toner-price').html(colorTonerPrice);
  return colorTonerPrice;
}

function updateRecommendServicePrice(serviceBumpedMarginPrice, totalMonthlyPages) {
  // supply only = 0
  if (mgmtAsmpts.contract_service_type === 'supplies_only' || serviceBumpedMarginPrice === 0 || totalMonthlyPages === 0) {
      $('#recommended-service-price').html('0');
      return 0;
  }

  let servicePrice = getRecommendServicePrice(serviceBumpedMarginPrice, totalMonthlyPages);
  $('#recommended-service-price').html(servicePrice);
  return servicePrice;
}

function getRecommendMonoTonerPrice(scaledTonerCPP, pages, monoCoverage) {
  // Pages * (CPP * Coverage / 0.05) / (1 - Toner Margin)
  return +(pages * (scaledTonerCPP * (monoCoverage / 0.05))).toFixed(4); // return float instead of string
}

function getRecommendColorTonerPrice(colorTonerMarginPrice, totalMonthlyColorPages, colorCoverage) {
  return +(colorTonerMarginPrice * totalMonthlyColorPages * colorCoverage / 0.05).toFixed(4);
  // return float instead of string
}

function getRecommendServicePrice(serviceBumpedMarginPrice, totalMonthlyPages) {
  return +(serviceBumpedMarginPrice * totalMonthlyPages).toFixed(4); // return float instead of string
}

function getRecommendMonoSalesPrice(monoTonerPrice, servicePrice, monoPages, colorPages) {
  return +((monoTonerPrice + (servicePrice * monoPages / (monoPages + colorPages))) / monoPages).toFixed(4);
  // return float instead of string
}

function updateRecommendColorSalesPrice(colorTonerPrice, servicePrice, monoPages, colorPages) {
  if (colorPages === 0) {
      $('#recommended-color-sales-price').html('0.0000');
      $('#recommended-color-sales-price2').val(0);
      $('#bundled-color-price').val(0);
      return 0;
  }

  let colorSalesPrice = getRecommendColorSalesPrice(colorTonerPrice, servicePrice, monoPages, colorPages);
  $('#recommended-color-sales-price').html(colorSalesPrice);
  $('#recommended-color-sales-price2').val(colorSalesPrice);
  if ( !$.trim($('#current-color-cpp').val())) {
      $('#current-color-cpp').val(colorSalesPrice);
  }

  // pre-calculate base rate  (gel 2019-11-25)
  if ( !$.trim($('#base-rate-color').val())) {
      $('#base-rate-color').val(($('#current-color-cpp').val() * page_cost_details.def_base_volume_color).toFixed(2));
  }

  $('#bundled-color-price').val(colorSalesPrice);
  return colorSalesPrice;
}

function updateRecommendMonthlyPrice(monoTonerPrice, colorTonerPrice, servicePrice) {
  let monthlyPrice = (monoTonerPrice + colorTonerPrice + servicePrice).toFixed(4);
  if (+monthlyPrice === 0) {
      $('#recommended-monthly-price').html('0');
      return 0;
  }

  $('#recommended-monthly-price').html(monthlyPrice);
  return +monthlyPrice;       // return float instead of string
}

function getRecommendColorSalesPrice(colorTonerPrice, servicePrice, monoPages, colorPages) {
  return +((colorTonerPrice + (servicePrice * colorPages / (monoPages + colorPages))) / colorPages).toFixed(4);
  // return float instead of string
}

function updateRecommendMonoSalesPrice(monoTonerPrice, servicePrice, monoPages, colorPages) {
  if (monoPages === 0) {
      $('#recommended-mono-sales-price').html('0.0000');
      $('#recommended-mono-sales-price2').val(0);
      $('#bundled-mono-price').val(0);
      return 0;
  }

  let monoSalesPrice = getRecommendMonoSalesPrice(monoTonerPrice, servicePrice, monoPages, colorPages);
  $('#recommended-mono-sales-price').html(monoSalesPrice);
  $('#recommended-mono-sales-price2').val(monoSalesPrice);
  if ( !$.trim($('#current-mono-cpp').val())) {
      $('#current-mono-cpp').val(monoSalesPrice);
  }

  // pre-calculate base rate  (gel 2019-11-25)
  if ( !$.trim($('#base-rate-mono').val())) {
      $('#base-rate-mono').val(($('#current-mono-cpp').val() * page_cost_details.def_base_volume_mono).toFixed(2));
  }

  $('#bundled-mono-price').val(monoSalesPrice);
  return monoSalesPrice;
}

function setDeviceSelectOptions(dropdown, printer_costs) {
  dropdown.empty();
  dropdown.append($('<option>', { value: -1, text: 'Select Device', selected: true, hidden: true }));
  for (let printer_cost in printer_costs) {
      dropdown.append($('<option>', { value: printer_costs[printer_cost].id, text: printer_costs[printer_cost].model_name }));
  }
}

function calculateMargin() {
  let runningMonoColorPriceLocal = 0;
  let runningMonoColorCostLocal = 0;
  let runningColorPriceLocal = 0;
  let runningColorCostLocal = 0;
  let runningMonoPriceLocal = 0;
  let runningMonoCostLocal = 0;
  for (let i of Object.keys(p_objects)) {
      let device = p_objects[i].service;
      // only include network devices
      if (device.is_non_network) continue;

      let serviceCost = parseFloat(device.service_cost) * (1 - mgmtAsmpts.target_margin_service);
      let totalPages = device.total_mono_pages + device.total_color_pages;
      if (device.is_color_device) {
          //================= monocolor
          let overage = device.total_mono_pages - device.base_volume_mono;

          let salesPrice = 0;
          if (!isNullOrWhitespace($('#monoColorCPP').val())) {
              salesPrice = parseFloat($('#monoColorCPP').val());
          } else {
              salesPrice = parseFloat(device.proposed_cpp_mono) > 0 ? parseFloat(device.proposed_cpp_mono) : parseFloat(device.rcmd_cpp_mono);
          }

          runningMonoColorPriceLocal += salesPrice * overage + parseFloat(device.base_rate_mono);

          let monoColorCost = parseFloat(device.mono_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
          runningMonoColorCostLocal += totalPages === 0 ? 0 : monoColorCost + (serviceCost * device.total_mono_pages / totalPages);

          //================= color
          overage = device.total_color_pages - device.base_volume_color;

          if (!isNullOrWhitespace($('#colorCPP').val())) {
              salesPrice = parseFloat($('#colorCPP').val());
          } else {
              salesPrice = parseFloat(device.proposed_cpp_color) > 0 ? parseFloat(device.proposed_cpp_color) : parseFloat(device.rcmd_cpp_color);
          }
          runningColorPriceLocal += salesPrice * overage + parseFloat(device.base_rate_color);

          let colorCost = parseFloat(device.color_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
          runningColorCostLocal += totalPages === 0 ? 0 : colorCost + (serviceCost * device.total_color_pages / totalPages);
      } else {
          //================= mono
          let overage = device.total_mono_pages - device.base_volume_mono;

          let salesPrice = 0;
          if (!isNullOrWhitespace($('#monoCPP').val())) {
              salesPrice = parseFloat($('#monoCPP').val());
          } else {
              salesPrice = parseFloat(device.proposed_cpp_mono) > 0 ? parseFloat(device.proposed_cpp_mono) : parseFloat(device.rcmd_cpp_mono);
          }
          runningMonoPriceLocal += salesPrice * overage + parseFloat(device.base_rate_mono);
          let monoCost = parseFloat(device.mono_toner_price) * (1 - mgmtAsmpts.target_margin_toner);
          runningMonoCostLocal += totalPages === 0 ? 0 : monoCost + (serviceCost * device.total_mono_pages / totalPages);
      }
  }

  monoMargin = runningMonoPriceLocal > 0 ? ((runningMonoPriceLocal - runningMonoCostLocal) / runningMonoPriceLocal * 100).toFixed(0) : 0;
  $('#monoMargin').text(monoMargin + '%');
  if (monoMargin / 100 < mgmtAsmpts.min_mono_margin) {
      $('#monoMargin').addClass('warning');
  } else {
      $('#monoMargin').removeClass('warning');
  }
  monoColorMargin = runningMonoColorPriceLocal > 0 ? ((runningMonoColorPriceLocal - runningMonoColorCostLocal) / runningMonoColorPriceLocal * 100).toFixed(0) : 0;
  $('#monoColorMargin').text(monoColorMargin + '%');
  if (monoColorMargin / 100 < mgmtAsmpts.min_mono_on_color_margin) {
      $('#monoColorMargin').addClass('warning');
  } else {
      $('#monoColorMargin').removeClass('warning');
  }
  colorMargin = runningColorPriceLocal > 0 ? ((runningColorPriceLocal - runningColorCostLocal) / runningColorPriceLocal * 100).toFixed(0) : 0;
  $('#colorMargin').text(colorMargin + '%');
  if (colorMargin / 100 < mgmtAsmpts.min_color_margin) {
      $('#colorMargin').addClass('warning');
  } else {
      $('#colorMargin').removeClass('warning');
  }
}

function updateMonthlyTotals() {
  let netPriceTotal = runningColorPrice + runningMonoPrice + runningMonoColorPrice;
  $('#monthlyNetPrice').text('$' + addThousandsSeparator(netPriceTotal.toFixed(2)));

  let netCostTotal = runningColorCost + runningMonoCost + runningMonoColorCost;
  let netMargin = netPriceTotal == 0 ? 0 : ((netPriceTotal - netCostTotal) / netPriceTotal * 100).toFixed(0);

  $('#netMargin').text(netMargin + '%');

  if (netMargin / 100 < (mgmtAsmpts.min_mono_margin + mgmtAsmpts.min_mono_on_color_margin + mgmtAsmpts.min_color_margin) / 3) {
      $('#netMargin').addClass('warning');
  } else {
      $('#netMargin').removeClass('warning');
  }

  let nonNetTotal = 0;
  $.each(p_objects, function (index, device) {
      device = device.service;
      if (!device.is_non_network) {
          return;
      }

      nonNetTotal += (device.non_network_cost * device.number_printers_serviced);
  });
  $('#monthlyNonNetPrice').text('$' + addThousandsSeparator(nonNetTotal.toFixed(2)));

  let monthlyLease = 0;
  let equipmentBought = 0;
  $.each(proposal_purchase_items, function (index, item) {
      if (item.buy_or_lease === 'buy') {
          equipmentBought += parseFloat(item.proposed_cost);
      } else {
          monthlyLease += parseFloat(item.lease_payment);
      }
  });
  $('#monthly-lease').text('$' + addThousandsSeparator(monthlyLease.toFixed(2)));
  $('#equipment-bought').text('$' + addThousandsSeparator(equipmentBought.toFixed(2)));
  
  let monthlyCommission = 0;
  let monthlyMPSCommission = 0;
  let monthlyEQCommission = 0;
      $.each(proposal_service_items, function (index, item) {
          monthlyMPSCommission += parseFloat(item.estimated_commission);
      });

      $.each(proposal_purchase_items, function (index, item) {
          monthlyEQCommission += parseFloat(item.estimated_commission);
      });

      monthlyCommission = monthlyMPSCommission + monthlyEQCommission;

  $('#total-monthly-commission').text('$' + addThousandsSeparator(monthlyCommission.toFixed(2)));
  $('#monthly-commission').text('$' + addThousandsSeparator(monthlyMPSCommission.toFixed(2)));
  $('#monthly-eq-commission').text('$' + addThousandsSeparator(monthlyEQCommission.toFixed(2)));

  let totalPrice = netPriceTotal + nonNetTotal + monthlyLease;
  $('#monthlyTotalPrice').text('$' + addThousandsSeparator(totalPrice.toFixed(2)));
}
// eslint-disable-next-line no-unused-vars
function requestStreetFighter() {
  $.ajax({
      type: 'POST',
      cache: false,
      data: {
          'proposal_id': proposal_id
      },
      url: window.location.origin + '/proposal/requestStreetFighterPricing/'
  }).done(function (response) {
      alert(response);
  }).fail(function (response) {
      alert(response.responseText);
  });
}

function updateOverallMargin() {
  $('#margin').val(($('#equipment-purchase-price').val() - $('#total-outcost').val()).toFixed(2));
  $('#margin-percentage').val(($('#margin').val() / $('#equipment-purchase-price').val() * 100).toFixed(2));
  if($('#leaseBuyout').val()===""){
      $('#leaseBuyout').val(0);
  }    
  if($('#equipment-purchase-price').val()===""){
      $('#equipment-purchase-price').val(0);
  }
  $('#leasePurchasePrice').val(1*$('#equipment-purchase-price').val()+1*$('#leaseBuyout').val());
  updateEquipmentCommissions();
}

function updateEquipmentCommissions(deviceType) {
  let NetEquipmentCommission = 0;

  switch (mgmtAsmpts.eq_commission_type) {
      case 'eq_flat_margin':
          NetEquipmentCommission = mgmtAsmpts.eq_percent_margin_flat_rate * $('#margin').val();
          $('#eqcommission').html(`${NetEquipmentCommission.toFixed(2)}`);
          break;
      case 'eq_flat_revenue':
          NetEquipmentCommission = mgmtAsmpts.eq_percentage_revenue_flat_rate * $('#equipment-purchase-price').val();
          $('#eqcommission').html(`${NetEquipmentCommission.toFixed(2)}`);
          break;
      case 'eq_blended_margin':
          NetEquipmentCommission = (deviceType == 'printer' ? mgmtAsmpts.eq_margin_rate_printers : mgmtAsmpts.eq_margin_rate_copiers) * $('#margin').val();
          $('#eqcommission').html(`${NetEquipmentCommission.toFixed(2)}`);
          break;
      case 'eq_blended_revenue':
          NetEquipmentCommission = (deviceType == 'printer' ? mgmtAsmpts.eq_revenue_rate_printers : mgmtAsmpts.eq_revenue_rate_copiers) * $('#equipment-purchase-price').val();
          $('#eqcommission').html(`${NetEquipmentCommission.toFixed(2)}`);
          break;
      default:
  
  }
}

function updatePObjects() {
  for(var i = 0; i < proposal_service_items.length; i++){
      let current_item =  proposal_service_items[i];
      if (!p_objects[current_item.id]) {
          p_objects[current_item.id] = {
              service: current_item,
              equipment: {}, //fill up later
              mono_tier: current_item.tier_level_mono,
              color_tier: current_item.tier_level_color
          };
      }
  }
}

function loadPrinterDetailsByMakeNN() {
  // Clear the shortName dropdown so selected make devices can be appended.
  $('#nonNetworkDevice-shortName').children().remove().end();

  $.ajax({
      type: 'GET',
      cache: false,
      url: window.location.origin + '/proposal/getPrinterDetailsByMake/' + $("#nonNetworkDevice-makeName :selected").val()
  }).done(function (response) {
      let printers = JSON.parse(response).printers;
      appendPrinterDetailsByMake($('#nonNetworkDevice-shortName'), printers);
  }).fail(function (error) {
      console.log(error);
  });
}

function loadPrinterDetailsByMake() {
  // Clear the shortName dropdown so selected make devices can be appended.
  $('#tcoDevice-shortName').children().remove().end();

  $.ajax({
      type: 'GET',
      cache: false,
      url: window.location.origin + '/proposal/getPrinterDetailsByMake/' + $("#tcoDevice-makeName :selected").val()
  }).done(function (response) {
      let printers = JSON.parse(response).printers;
      appendPrinterDetailsByMake($('#tcoDevice-shortName'), printers);
  }).fail(function (error) {
      console.log(error);
  });
}

function appendPrinterDetailsByMake(deviceDropDown, printers) {
  deviceDropDown.append($('<option>', { value: -1, text: '', hidden: true }));
  for (let i = 0; i < printers.length; i++) {
      let printer = printers[i];
      deviceDropDown.append($('<option>', { value: printer[0], text: printer[1] }));
  }
}

$('#tcoDevice-shortName').on('change', function () {
  // When a model is changed, force all values to default   (GEL 12/29/2019)
  $('#tcoDevice-quantity').val('1');
  $('#tcoDevice-totalOutcost').val('');
  $('#tcoDevice-totalOutcost').prop('disabled', true);
  $('#tcoDevice-purchasePrice').val('');
  $('#tcoDevice-purchasePrice').prop('disabled', true);
  $('#total-monthly-mono-pages').val('');
  $('#total-monthly-color-pages').val('');
  $('#total-monthly-pages').val('');
  $('#mono-coverage').val('.05');
  $('#color-coverage').val('.05');
  $('#color-coverage').prop('disabled', true);
  $('#recommended-mono-toner-price').html('0');
  $('#recommended-color-toner-price').html('0');
  $('#recommended-service-price').html('0');
  $('#recommended-monthly-price').html('0');
  $('#recommended-mono-sales-price').html('0.0000');
  $('#recommended-color-sales-price').html('0.0000');
  $('#bundled-monthly-mono-pages').val('');
  $('#bundled-monthly-color-pages').val('');
  $('#recommended-mono-sales-price2').val(0);
  $('#recommended-color-sales-price2').val(0);
  $('#bundled-mono-price').val(0);
  $('#bundled-color-price').val(0);
  $('#bundled-mono-monthly').val(0);
  $('#bundled-color-monthly').val(0);
  $('#bundledAmt').val(0);
  $('#base-volume-mono').val('');
  $('#base-volume-color').val('');
  $('#base-volume-color').prop('disabled', true);
  $('#base-rate-mono').val('');
  $('#base-rate-color').val('');
  $('#base-rate-color').prop('disabled', true);
  $('#current-mono-cpp').val('');
  $('#current-color-cpp').val('');
  // end (GEL 12/29/2019)
  $('#equipment-options').prop('disabled', false);
  if ($(this).val() !== '-1') {
      getNetDeviceDetails($(this).val());
  }
  $('#add-tco-device').removeAttr('disabled');
  $('#equipment-options-title').html(this.options[this.selectedIndex].innerHTML);

  // clear any previous equipment options
  clearEquipmentOptionsValues();
});

function getNetDeviceDetails(deviceId) {
  $.ajax({
      type: 'POST',
      cache: false,
      data: { 'device_id': deviceId, 'proposal_id': proposal_id },
      url: window.location.origin + '/proposal/getNetworkDeviceDetails/'
  }).done(function (response) {
      printer_costs = response.printer_costs;
      printer_details = response.printer_details;
      toner_costs = response.toners_costs;
      accessories = response.accessories;
      page_cost_details = response.page_cost_details;

      if (toner_costs.warning) {
          alert('No available toner for this printer model. Check with your manager.');
      }

      // Allow pricing display to toggle on/off per Harry (GEL 2019-08-27)
      var show_pricing = false;
      if (show_pricing == true) {
          $('#show-pricing').removeClass('hide');
      }
      // Default in average monthly volumes for mono and color (GEL 2019-08-31)
      // Update base volume mono   (GEL 2019-11-20)
      // Implement the auto-populate volume and rate calculation (GEL 2019-12-05)
      if(modal_mode == 'new') {
          $('#total-monthly-mono-pages').val(printer_details.avm_mono);
          $('#bundled-monthly-mono-pages').val(printer_details.avm_mono);
          if ( $('#base-volume-mono').val() ) {
              
          } else {
              if (proposal_settings.auto_pop_base) {
                  $('#base-volume-mono').val(page_cost_details.def_base_volume_mono);
              } else {
                  $('#base-volume-mono').val(0);
                  $('#base-rate-mono').val(0);
              }    
          } 
          $('#current-mono-cpp').val('');
          $('#current-color-cpp').val('');
      }

      if (printer_details.printer_is_color_type == true) {
          $('#lock-margin-option').removeClass('hide');
          $('#total-monthly-color-pages').parent().parent().removeClass('hide');
          $('#bundled-monthly-color-pages').parent().parent().removeClass('hide');
          $('#bundled-color-section').removeClass('hide');
          $('#color-coverage').parent().parent().parent().removeClass('hide');
          $('#rcmdp-color-toner').parent().removeClass('hide');
          $('#rcmdp-color-sales').parent().removeClass('hide');
          $('#base-volume-color').parent().parent().removeClass('hide');
          $('#base-rate-color').parent().parent().parent().removeClass('hide');
          $('#current-color-cpp').parent().parent().parent().removeClass('hide');
          $('#lock-margin').attr('disabled', false);
          if($('#lock-margin').val() == '1') {
              $('#total-monthly-mono-pages').attr('disabled', true);
              $('#total-monthly-color-pages').attr('disabled', true);                
          } else {
              $('#total-monthly-mono-pages').attr('disabled', false);
              $('#total-monthly-color-pages').attr('disabled', false);  
          $('#total-monthly-color-pages').attr('disabled', false);
              $('#total-monthly-color-pages').attr('disabled', false);  
          }
          if(modal_mode == 'new') {
              $('#total-monthly-color-pages').val(printer_details.avm_color);
              $('#bundled-monthly-color-pages').val(printer_details.avm_color);
              // add conditional when autopopbase is false set to zero
              if (proposal_settings.auto_pop_base) {
                  $('#base-volume-color').val(page_cost_details.def_base_volume_color);
              } else {
                  $('#base-volume-color').val(0);
                  $('#base-rate-color').val(0);
              }
          }
          $('#color-coverage').attr('disabled', false);
          $('#base-volume-color').attr('disabled', false);
          $('#base-rate-color').attr('disabled', false);
          $('#current-color-cpp').attr('disabled', false);
      } else {
          // update the hidden values for the calculation
          $('#total-monthly-color-pages').val(0);
          $('#bundled-monthly-color-pages').val(0);
          $('#base-volume-color').val(0);
          $('#base-rate-color').val(0);
          $('#current-color-cpp').val(0);
          // remove all color related rows
          $('#lock-margin-option').addClass('hide');
          $('#total-monthly-color-pages').parent().parent().addClass('hide');
          $('#bundled-monthly-color-pages').parent().parent().addClass('hide');
          $('#bundled-color-section').addClass('hide');
          $('#color-coverage').parent().parent().parent().addClass('hide');
          $('#rcmdp-color-toner').parent().addClass('hide');
          $('#rcmdp-color-sales').parent().addClass('hide');
          $('#base-volume-color').parent().parent().addClass('hide');
          $('#base-rate-color').parent().parent().parent().addClass('hide');
          $('#current-color-cpp').parent().parent().parent().addClass('hide');
          $('#lock-margin').attr('disabled', true);
          if($('#lock-margin').val() == '1') {
              $('#total-monthly-mono-pages').attr('disabled', true);              
          } else {
              $('#total-monthly-mono-pages').attr('disabled', false);  
          }
          $('#total-monthly-color-pages').attr('disabled', true);
          $('#color-coverage').attr('disabled', true);
          $('#base-volume-color').attr('disabled', true);
          $('#base-rate-color').attr('disabled', true);
          $('#current-color-cpp').attr('disabled', true);
      }

      $('#total-monthly-mono-pages').trigger('input');
      setDeviceSelectOptions($('#device-dropdown1'), printer_costs);
  }).fail(function (xhr, status, e) {
      alert(xhr + ' ' + status + ' ' + e);
  });
}

function clearEquipmentOptionsValues() {
  let zero = '0.00';
  $('#device-dropdown1').val(-1);
  $('#deviceOutcost1').val(zero);
  $('#deviceMsrp1').val(zero);
  $('#total-outcost').val(zero);
  $('#total-msrpcost').val(zero);
  $('#equipment-purchase-price').val(zero);
  $('#margin').val(zero);
  $('#margin-percentage').val(zero);
  $('.accessory-row').remove();
  $('#addAccessory1').prop('disabled', true);
//    $('#monthly-payment').val(0);
  $('#buy-lease').val('buy');
  $('#lock-margin').val(0);
}

function appendToTCOTable(newDevice, purchase_item_id) {
  network_devices.push(newDevice);
  const { current_cpp_mono: monoCPP, current_cpp_color: colorCPP } = newDevice;

  // Update UI with buy/lease and price for purchased/leased equipment (GEL 2019-11-20)
  let purchaseDevice;
  let buy_or_lease = '-';
  let proposed_cost = '0.00';
  // todo optimize the following code... 
  if (purchase_item_id === "") {
      purchase_item_id = null;
  };
  if (purchase_item_id != null) {
      purchaseDevice = loadProposalPurchaseItem(purchase_item_id);
      buy_or_lease = purchaseDevice.buy_or_lease;
      proposed_cost = addThousandsSeparator(parseFloat(purchaseDevice.proposed_cost).toFixed(2));
  } else if (newDevice.proposal_purchase_item_id != null) {
      purchaseDevice = loadProposalPurchaseItem(newDevice.proposal_purchase_item_id);
      buy_or_lease = purchaseDevice.buy_or_lease;
      proposed_cost = addThousandsSeparator(parseFloat(purchaseDevice.proposed_cost).toFixed(2)); 
  } else {
      buy_or_lease = '-';
      proposed_cost = '0.00';
  };

  let currentRow = tco_table.row.add(
      [
          newDevice.short_model,
          addThousandsSeparator(newDevice.number_printers_serviced == 0 ? '---' : newDevice.number_printers_serviced),
          newDevice.monthly_lease_payment ? 0 : addThousandsSeparator(parseFloat(newDevice.monthly_lease_payment).toFixed(2)),
          addThousandsSeparator(newDevice.total_mono_pages == 0 ? '---' : newDevice.total_mono_pages),
          addThousandsSeparator(newDevice.total_color_pages == 0 ? '---' : newDevice.total_color_pages),
          addThousandsSeparator(newDevice.base_volume_mono == 0 ? '---' : newDevice.base_volume_mono),
          newDevice.base_rate_mono == 0 ? '---' : ('$' + addThousandsSeparator(parseFloat(newDevice.base_rate_mono).toFixed(2))),
          addThousandsSeparator(newDevice.base_volume_color == 0 ? '---' : newDevice.base_volume_color),
          newDevice.base_rate_color == 0 ? '---' : ('$' + addThousandsSeparator(parseFloat(newDevice.base_rate_color).toFixed(2))),
          addThousandsSeparator(monoCPP),
          addThousandsSeparator(colorCPP),
          '<button id="edit-button" data-type="edit-device"><i class="fas fa-edit size-14"></i></button><button data-type="remove-device"><i class="fas fa-trash-alt size-14"></i></button>'
      ]
  ).draw().node();

  $(currentRow)[0].cells[2].classList.add('monthly-lease-payment')
  $("#edit-button").parent().css('padding', '0')

  $(currentRow).attr('id', newDevice.id);
  $(currentRow).dblclick(function () {
      loadTCODeviceModal(newDevice.id);
      $('#addTCODevice').foundation('open');
  });

  updateCostSummary();
}

function loadTCODeviceModal(id) {
  modal_mode = 'edit';
  const p = p_objects[id];

  $('#tcoDevice-shortName').val(p.service.printer_id);
  $('#tcoDevice-shortName').trigger('change');
  $('#tcoDevice-shortName').prop('disabled', true);

  $('#tcoDevice-quantity').val(p.service.number_printers_serviced);

  $('#total-monthly-mono-pages').val(p.service.total_mono_pages);
  $('#bundled-monthly-mono-pages').val(p.service.total_mono_pages);
  $('#mono-coverage').val(p.service.mono_coverage.toFixed(2).replace('0.', '.'));

  // add conditional when autopopbase is false set to zero
  if (proposal_settings.auto_pop_base) {
      $('#base-volume-mono').val(page_cost_details.def_base_volume_mono);
  } else {
      $('#base-volume-mono').val(0);
  }
  //$('#base-volume-mono').val(p.service.base_volume_mono);
  $('#base-rate-mono').val(p.service.base_rate_mono);
  $('#current-mono-cpp').val(p.service.proposed_cpp_mono);

  if (p.service.is_color_device) {
      $('#total-monthly-color-pages').val(p.service.total_color_pages);
      $('#bundled-monthly-color-pages').val(p.service.total_color_pages);
      $('#color-coverage').val(p.service.color_coverage.toFixed(2).replace('0.', '.'));
      // add conditional when autopopbase is false set to zero (GEL 2019-12-05)
      if (proposal_settings.auto_pop_base) {
          $('#base-volume-color').val(page_cost_details.def_base_volume_color);
      } else {
          $('#base-volume-color').val(0);
      }
      //$('#base-volume-color').val(p.service.base_volume_color);
      $('#base-rate-color').val(p.service.base_rate_color);
      $('#current-color-cpp').val(p.service.proposed_cpp_color);
  }

  $('#add-tco-device').prop('disabled', false);
  $('#add-tco-device').html('Save');
  $('#add-tco-device').data('id', p.service.id);
  $('#total-monthly-mono-pages').trigger('input');

}

const updateCostSummary = () => {
  const base_on = $('#baseSummaryOn').val();

  const currentMonthlySpend = base_on === 'device_list' ? monthlySpendByDevice() : monthlySpendByAnnualAssumptions();

  const proposedMonthlySpend = mps_price + monthly_lease;

  const annualSavings = 12 * (currentMonthlySpend - proposedMonthlySpend);

  const contractSavings = proposal_term * (annualSavings / 12);

  $('#currentMonthlySpend').val(currentMonthlySpend.toFixed(2));
  $('#proposedMonthlySpend').val(proposedMonthlySpend.toFixed(2));
  $('#annualSavings').val(annualSavings.toFixed(2));
  $('#savingsOverContractLife').val(contractSavings.toFixed(2));
}



const monthlySpendByDevice = () => {
  let monthlySpend = 0;

  $('#tco-devices-table tbody tr').each(function() {
    const baseRateAmount = Number($(this).find('.base-rate-mono').text()) + Number($(this).find('.base-rate-color').text());
    const overageMono = Math.max(0, Number($(this).find('.monthly-mono').text()) - Number($(this).find('.base-volume-mono').text()));
    const overageColor = Math.max(0, Number($(this).find('.monthly-color').text() - Number($(this).find('.base-rate-color').text())));

    const overageMonoCost = Number($(this).find('.current-mono-cpp').text()) * overageMono;
    const overageColorCost = Number($(this).find('.current-color-cpp').text()) * overageColor;

    const deviceSpend = Number($(this).find('monthly-lease-payment').text()) + baseRateAmount + overageMonoCost + overageColorCost

    monthlySpend += deviceSpend;
  });

  return monthlySpend;
}

const monthlySpendByAnnualAssumptions = () => {
  const totalSupplySpend = Number($('#currentTotalSupplySpend').val());
  const totalServiceSpend = Number($('#currentTotalServiceSpend').val());
  const totalLeaseSpend = Number($('#currentTotalLeaseSpend').val());
  const burdenRate = Number($('#currentTransactionCost').val());
  const annualSupplyCount = Number($('#currentSalesOrderCount').val());
  const annualServiceCount = Number($('#currentServiceOrderCount').val());

  const annualSpend = totalSupplySpend + totalServiceSpend + totalLeaseSpend + burdenRate * (annualSupplyCount + annualServiceCount);
  const monthlySpend = annualSpend / 12;

  return monthlySpend;
}

$("#client-content2").change(() => {
  updateCostSummary();
});

$("#baseSummaryOn").change(() => {
  updateCostSummary();
});