var proposal_id = window.location.pathname.split('/')[3];
var level = 4;

$(document).ready(function (){
    // add all of the management assumption booleans (GEL 2019-08-31)
    var company_settings ="";
    company_settings = loadManagementSettings(proposal_details.assumptions_id);
    allow_cartridge_pricing = company_settings.allow_cartridge_pricing;
    cpc_toner_only = company_settings.cpc_toner_only;
    allow_leasing = company_settings.allow_leasing;
    allow_rental = company_settings.allow_rental;
    allow_reman = company_settings.allow_reman;
    allow_tiered = company_settings.allow_tiered;
    allow_flat_rate = company_settings.allow_flat_rate;
    allow_term_offsets = company_settings.allow_term_offsets;
    allow_tco = company_settings.allow_tco;
    target_margin_service = company_settings.target_margin_service;
    
    proposal_items = loadProposalItems(proposal_id);
    item_count = proposal_items.service_item_count;
    if (item_count > 0) {
        $("#proposalDetails").addClass("disabledbutton");
    }
    if (item_count = 0) {
        $("#proposalDetails").removeClass("disabledbutton");
    }

    if (allow_tco) {
        $('#tco-button3').show();
    } else {
        $('#tco-button3').hide();
    }

    loadDetailOptions(proposal_details, company_settings);
});

// insert function to retrieve allowed feature list (GEL 2019-08-31)
function loadManagementSettings(assumptions_id) {
    var return_data;
    $.ajax({
        type: 'GET',
        async: false,
        cache: false,
        url: window.location.origin + '/proposal/getManagementSettings/' + assumptions_id
    }).done(function (response) {
        return_data = JSON.parse(response);
    }).fail(function (error) {
        alert(error);
    });
    return return_data;
}

// insert function to retrieve proposal item count (GEL 2019-10-11)
function loadProposalItems(proposal_id) {
    var return_data;
    $.ajax({
        type: 'GET',
        async: false,
        cache: false,
        url: window.location.origin + '/proposal/getProposalItems/' + proposal_id
    }).done(function (response) {
        return_data = JSON.parse(response);
    }).fail(function (error) {
        alert(error);
    });
    return return_data;
}

function loadDetailOptions(details, company_settings) {
    if (details.term != -1) {
        $('#termSelect option[value="' + details.term + '"]').prop('selected', true);
    }
    if (details.contractType != -1) {
        $('#contractTypeSelect option[value="' + (details.contractType) + '"]').prop('selected', true);
    }
    if (details.propOutsideLoc != -1) {
        let zone0 = 100 - (100*$('#zone01Select').val() + 100*$('#zone02Select').val() + 100*$('#zone03Select').val());
        $('#proportionSelect').val(zone0 / 100);
        $('#zone01Select option[value="' + details.zone_01 + '"]').prop('selected', true);
        $('#zone02Select option[value="' + details.zone_02 + '"]').prop('selected', true);
        $('#zone03Select option[value="' + details.zone_03 + '"]').prop('selected', true);
    }

    // Implement multiple services zones (GEL 2019-09-18)
    let zone0 = 100 - (100*$('#zone01Select').val() + 100*$('#zone02Select').val() + 100*$('#zone03Select').val());
    $('#proportionSelect').val(zone0 / 100);
    // Zone3 - on change check non-local zones to not exceed 100% and adjust zone0 to be the difference. 
    $("#zone03Select").on('change', function() {
        let zone0=100*$('#proportionSelect').val();
        let zone1=100*$('#zone01Select').val();
        let zone2=100*$('#zone02Select').val();
        let zone3=100*$('#zone03Select').val();
        if (zone1+zone2+zone3 > 100) {
            zone3 = 100 - (zone1 + zone2);
            alert("Hi there... the boss says your non-local zone percents can't add up to more than 100.  Your change to zone 3 put you over the limit, so we dropped it down to make the numbers add up.  Hope you don't mind!!!");
            $('#zone03Select').val(zone3 / 100);
        };
        zone0 = 100 - (zone1 + zone2 + zone3);
        $('#proportionSelect').val(zone0 / 100);
    })
    // Zone2 - on change check non-local zones to not exceed 100% and adjust zone2 to be the difference.
    $("#zone02Select").on('change', function() {
        let zone0=100*$('#proportionSelect').val();
        let zone1=100*$('#zone01Select').val();
        let zone2=100*$('#zone02Select').val();
        let zone3=100*$('#zone03Select').val();
        if (zone1+zone2+zone3 > 100) {
            zone2 = 100 - (zone1 + zone3);
            alert("Oops! The change to zone 2 made the non-local zones sum up to more than 100%... so we decreased it a little.  To get it any higher you should decrease one or more of the other zones percentages.");
            $('#zone02Select').val(zone2 / 100);
        };
        zone0 = 100 - (zone1 + zone2 + zone3);
        $('#proportionSelect').val(zone0 / 100);
    })
    // Zone1 - on change check non-local zones to not exceed 100% and adjust zone1 to be the difference.
    $("#zone01Select").on('change', function() {
        let zone0=100*$('#proportionSelect').val();
        let zone1=100*$('#zone01Select').val();
        let zone2=100*$('#zone02Select').val();
        let zone3=100*$('#zone03Select').val();
        if (zone1+zone2+zone3 > 100) {
            zone1 = 100 - (zone2 + zone3);
            alert("Hmmm.... It looks like the zone 1 change made the non-local zones total higher than 100%.  We adjusted it down to keep everything in balance.  To get it any higher you will need to decrease one or more of the other zones.");
            $('#zone01Select').val(zone1 / 100);
        }
        zone0 = 100 - (zone1 + zone2 + zone3);
        $('#proportionSelect').val(zone0 / 100);
    })
    // toggle OEM, OEM SMP, REMAN visibility on/off  (GEL 2019-09-13)
    if (company_settings.allow_reman) {
        $('#mfrButton-1').show();
        $('#manufacturerSelect').show();
    } else {
        $('#mfrButton-1').hide();
        $('#manufacturerSelect').hide();
    };

    if (details.serviceLevel != -1) {
        switch (details.serviceLevel) {
            case 'Silver':
                level = 24;
                break;
            case 'Gold':
                level = 4;
                break;
            case 'Platinum':
                level = 2;
                break;
        }
        $('#serviceLevelSelect option[value="' + level + '"]').prop('selected', true);
    }

    if (details.auto_pop_base) {
      $('#autopopbase option[value="1"]').prop('selected', true); 
    } else {
      $('#autopopbase option[value="0"]').prop('selected', true);
    }
}


$("#locationTT").attr('title', 'These fields help adjust service costs depending on trip distance.');
$('#zone01Select').attr('title', 'Enter the percent of devices 80-160 km (50-100 miles) from where service will be dispatched');
$('#zone02Select').attr('title', 'Enter the percent of devices 160-240 km (100-150 miles) from where service will be dispatched');
$('#zone03Select').attr('title', 'Enter the percent of devices more than 240 km (150 miles) from where service will be dispatched');
$('#autopopbase').attr('title', 'Allows default base volumes to load automatically when adding devices');

$('#previous-page').on('click', function(){
    window.location.href = window.location.origin + '/proposal/selectClient/'+ parseInt(proposal_id);
});

$('#save-details').on('click', function() {
    saveProposal('save');
});

$('#continue-details').on('click', function() {
    saveProposal('continue');
});

function saveProposal(btn) {
  return new Promise((resolve, reject) => {
    let serviceLevel = function () {
      switch ($('#serviceLevelSelect').val()) {
        case '2':
            return 'Platinum';
        case '4':
            return 'Gold';
        case '24':
            return 'Silver';
      }
    };

    proposal_data = {
        'term': parseInt($('#termSelect').val()),
        'contract_service_type': $('#contractTypeSelect').val(),
        'default_toner_type': $('#manufacturerSelect').val(),
        // Note that proportion_fleet_offsite now stores the "local" percent rather than offsite and is for display purposes only
        'proportion_fleet_offsite': (100 - (100 * parseFloat($('#proportionSelect').val()))) / 100,
        'contract_service_level': serviceLevel(),
        // The zone fields now store the offsite device percentages
        'zone_01': (100 * parseFloat($('#zone01Select').val())) / 100,
        'zone_02': (100 * parseFloat($('#zone02Select').val())) / 100,
        'zone_03': (100 * parseFloat($('#zone03Select').val())) / 100,
        'auto_populate_base_info': Boolean(parseInt($('#autopopbase').val()))
    };

    $.ajax({
        type: 'POST',
        cache: false,
        data: {
            'proposal_data': JSON.stringify(proposal_data),
            'proposal_id': proposal_details.proposal_id
        },
        url: window.location.origin + '/proposal/details/saveProposal/',
        error: function (xhr, status, e) {
            alert(xhr + ' ' + status + ' ' + e);
            reject(e);
        }
    }).done (function(response) {
        if (btn == 'save') {
            window.location.href = '/repDashboard';
        } else if (btn == 'continue') {
            window.location.href = '/proposal/pricing/' + parseInt(response.proposal_id);
        } else if (btn == 'dca') {
            // do nothing
        } else {
            alert('Warning!!!');
        }
        resolve();
    });
  });
}

const getAccounts = async (proposalId) => {
  await saveProposal('dca');
  $('#importDCA-header').text('Select an Account');
  const modal = document.getElementById('importDCAModalContent');
  modal.innerHTML = '<div>Loading...</div>';
  try {
    const request = await fetch(window.location.origin + `/dca/accounts/${proposalId}`);
    const response = await request.json();

    if (request.status === 401) {
      modal.innerHTML = `<div>${JSON.parse(response)}</div>`;
      return;
    }
    const accounts = JSON.parse(response);

    let modalHTML = '';
    accounts.forEach(account => {
      modalHTML += accountHTML(account);
    });

    modal.innerHTML = modalHTML;
  } catch(error) {
    console.error(error);
    modal.innerHTML = '<div>Sorry, an error occurred.</div>'
  }
}

const getDeviceInfoForAccount = async (accountId) => {
  const modal = document.getElementById('importDCAModalContent');
  modal.innerHTML = '<div>Loading...</div>';

  try {
    const request = await fetch(window.location.origin + `/dca/device-info/${accountId}`);
    const response = await request.json();
    const devices = JSON.parse(response);

    if (jQuery.isEmptyObject(devices)) {
      modal.innerHTML = `<div>Sorry, no devices were found for the selected account.</div>`;
    } else {
      let devicesHTML = '';
      Object.keys(devices).forEach(device => devicesHTML += deviceHTML(device));
      devicesHTML += `<a class="import-devices-button button" onclick="getDeviceData(${accountId})">Import Selected Devices</a>`;

      $('#importDCA-header').text('Select Devices for Proposal');
      modal.innerHTML = devicesHTML;
    }
  } catch(error) {
    modal.innerHTML = '<div>Sorry, an error occurred.</div>';
    console.error(error);
  }
}

const getDeviceData = async accountId => {
  $('#importDCA-header').text('Importing Devices for Proposal');
  const modal = document.getElementById('importDCAModalContent');
  const devices = [...document.getElementsByClassName('device-selected')].map(device => device.innerText);
  modal.innerHTML = '<div>Loading...</div>';
  try {
    const cookie = document.cookie.split('csrftoken=')[1].split(';')[0];
    const request = await fetch(window.location.origin + `/dca/device-data/${accountId}`, {
      method: 'POST',
      body: JSON.stringify({devices}),
      headers: { "X-CSRFToken": cookie },
    });
    const response = await request.json();

    const message = JSON.parse(response);

    modal.innerHTML = `<div>${message}</div>`;

  } catch(error) {
    modal.innerHTML = '<div>Sorry, an error occurred.</div>';
    console.error(error);
  }
}

const toggleDevice = event => {
  const enabled = $(event.currentTarget).attr('class').includes('device-selected');

  if (enabled) {
    $(event.currentTarget).removeClass('device-selected');
    $(event.currentTarget).next().removeClass('device-name');
  }
  else {
    $(event.currentTarget).addClass('device-selected');
    $(event.currentTarget).next().addClass('device-name');
  }

}

const accountHTML = accountInfo => {
  return `
    <div class='select-item' onclick='getDeviceInfoForAccount(${accountInfo["AccountID"]})'>${accountInfo["Name"]}</div>
  `;
}

const deviceHTML = deviceName => {
  return `
    <div onclick="toggleDevice(event)" class="device device-selected">
      <div class="device-name">${deviceName}</div>
    </div>
  `;
}


const ConnectPrintFleet = async (proposalId) => {
  await saveProposal('dca');
  $('#importDCA-header').text('Select an Group/Account');
  const modal = document.getElementById('importDCAModalContent');
  modal.innerHTML = '<div>Loading...</div>';
  try {
    const request = await fetch(window.location.origin + `/print_fleet/groups/${proposalId}`);
    const response = await request.json();

    if (request.status === 401) {
      modal.innerHTML = `<div>${JSON.parse(response)}</div>`;
      return;
    }
    const accounts = JSON.parse(response);

    let modalHTML = '';
    accounts.forEach(account => {
      console.log(account);
      modalHTML += accountHTMLPF(account);
    });

    modal.innerHTML = modalHTML;
  } catch(error) {
    console.error(error);
    modal.innerHTML = '<div>Sorry, an error occurred.</div>'
  }
}

const getDeviceInfoForGroup = async (groupId) => {
  const modal = document.getElementById('importDCAModalContent');
  modal.innerHTML = '<div>Loading...</div>';

  try {
    const request = await fetch(window.location.origin + `/print_fleet/devices/${groupId}`);
    const response = await request.json();
    const devices = JSON.parse(response);

    if (jQuery.isEmptyObject(devices)) {
      modal.innerHTML = `<div>Sorry, no devices were found for the selected account.</div>`;
    } else {
      let devicesHTML = '';

      devices.forEach(device => devicesHTML += deviceHTMLPF(device));

      devicesHTML += `<a class="import-devices-button button" onclick='getDeviceDataPF("${groupId}")'>Import Selected PF Devices</a>`;

      $('#importDCA-header').text('Select Device for Proposal');
      modal.innerHTML = devicesHTML;
    }
  } catch(error) {
    modal.innerHTML = '<div>Sorry, an error occurred.</div>';
    console.error(error);
  }
}

const parseGroup = async (account) => {
//  TODO
//  await saveProposal('dca');
  $('#importDCA-header').text('Select an Group/Account');
  const modal = document.getElementById('importDCAModalContent');
  modal.innerHTML = '<div>Loading...</div>';

  try {
    const request = await fetch(window.location.origin + `/print_fleet/group/${account}`);
    const response = await request.json();

    if (request.status === 401) {
      modal.innerHTML = `<div>${JSON.parse(response)}</div>`;
      return;
    }
    const group = JSON.parse(response);

    if (group['children'].length > 0) {
        let modalHTML = getDeviceInfoForGroupHTMLPF(group);

        group['children'].forEach(child => modalHTML +=
            accountHTMLPF(child)
            );
        modal.innerHTML = modalHTML;
      }
      else {
        let modalHTML = '';
        modalHTML += getDeviceInfoForGroupHTMLPF(group);
        modal.innerHTML = modalHTML;
      }

  } catch(error) {
    console.error(error);
    modal.innerHTML = '<div>Sorry, an error occurred.</div>'
  }
}

const accountHTMLPF = accountInfo => {
      return `
        <div class='select-item' onclick='parseGroup("${accountInfo["id"]}")'>${accountInfo["name"]}</div>
      `;
}

const deviceHTMLPF__ = device => {
  return `
    <div class='select-item' onclick='getDeviceInfo("${device["id"]}")'>${device["name"]}</div>
  `;
}

const deviceHTMLPF = device => {
  return `
    <div onclick="toggleDevice(event)" class="device device-selected">
      <div class="device-name">${device}</div>
    </div>
  `;
}

const getDeviceInfoForGroupHTMLPF = group => {
  return `
    <div class='select-item' onclick='getDeviceInfoForGroup("${group["id"]}")'>${group["name"]}</div>
  `;
}

const getDeviceInfo = async (deviceId) => {
  const modal = document.getElementById('importDCAModalContent');
  modal.innerHTML = '<div>Loading...</div>';

  try {
    const request = await fetch(window.location.origin + `/print_fleet/device_info/${deviceId}`);
    const response = await request.json();
    const device_info = JSON.parse(response);

    if (jQuery.isEmptyObject(device_info)) {
      modal.innerHTML = `<div>Sorry, no meters were found for the selected device.</div>`;
    } else {
      let devicesHTML = '';

      device_info.forEach(info => devicesHTML +=
        `<div onclick="toggleDevice(event)" class="device device-selected">
        <div class="device-info">${info["label"]}</div>
        </div>`
      );


      $('#importDCA-header').text('');
      modal.innerHTML = devicesHTML;
    }
  } catch(error) {
    modal.innerHTML = '<div>Sorry, an error occurred.</div>';
    console.error(error);
  }
}

const getDeviceDataPF = async groupId => {
  $('#importDCA-header').text('Importing Devices for Proposal');
  const modal = document.getElementById('importDCAModalContent');
  const devices = [...document.getElementsByClassName('device-selected')].map(device => device.innerText);
  modal.innerHTML = '<div>Loading...</div>';
  try {
    const cookie = document.cookie.split('csrftoken=')[1].split(';')[0];
    const request = await fetch(window.location.origin + `/print_fleet/device_data/${groupId}`, {
      method: 'POST',
      body: JSON.stringify({devices}),
      headers: { "X-CSRFToken": cookie },
    });

    const response = await request.json();
    const message = JSON.parse(response);

    modal.innerHTML = `<div>${message}</div>`;

  } catch(error) {
    modal.innerHTML = '<div>Sorry, an error occurred.</div>';
    console.error(error);
  }
}