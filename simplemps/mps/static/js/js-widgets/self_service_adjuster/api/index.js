import React from 'react';
import axios from 'axios';
import { getRecommendedPricing, getProposedCost, isDef } from '../src/utilities';
import { isEmpty } from 'ramda';
/**
 * Add Network device to proposal
 */
const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};
/**
 * Remove the device from the proposal purchase items.
 * 
 * @param { Integer } device_id 
 */
export const removeNetworkDevice = async (device_id, proposal_id) => {
    const csrftoken = getCookie('csrftoken');
    const params = new URLSearchParams();
    params.append('id', device_id);

    const removeDevice = await axios.post(window.location.origin + '/proposal/removeNetworkDevice/' + proposal_id + '/', params, { 
        headers: { 
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken }
    })

    return removeDevice;
}
export const addNetworkDevice = async (device, specs, proposal_id, is_network) => {
    const csrftoken = getCookie('csrftoken');
    let proposed_non_network_service = {};
    
    if(!is_network) {
        proposed_non_network_service = {
            printer: parseInt(device.printer_id),
            number_printers_serviced: parseInt(specs.quantity),
            non_network_cost: parseFloat(device.is_non_network.non_network_unit_price).toFixed(4), // unit price maybe?
            mono_coverage: '0.05',
            color_coverage: '0.05',
            estimated_commission: parseFloat(device.is_non_network.non_network_details.non_network_commission).toFixed(4),
            is_non_network: !is_network,
            total_color_pages: specs.color,
            total_mono_pages: specs.mono,
        }
    } else {
        proposed_non_network_service = {
            printer: parseInt(device.printer_id),
            number_printers_serviced: parseInt(specs.quantity),
            non_network_cost: 0,
            // default coverage
            mono_coverage: '0.05',
            color_coverage: '0.05',
            estimated_commission: 0,
            is_non_network: !is_network,
            proposed_cpp_mono: parseFloat(device.rcmdPricing.sf_mono_price).toFixed(4),
            proposed_cpp_color: parseFloat(device.rcmdPricing.sf_color_price).toFixed(4),
            rcmd_cpp_mono: parseFloat(device.rcmdPricing.rcmdMonoToner).toFixed(4),
            rcmd_cpp_color: parseFloat(device.rcmdPricing.rcmdColorToner).toFixed(4),
            total_color_pages: specs.color * specs.quantity,
            total_mono_pages: specs.mono * specs.quantity,
            base_volume_mono: device.page_details.def_base_volume_mono,
            base_volume_color: device.page_details.def_base_volume_color,
            base_rate_mono: device.page_details.def_base_rate_mono,
            base_rate_color: device.page_details.def_base_rate_color,
            mono_toner_price: parseFloat(device.rcmdPricing.rcmdMonoToner).toFixed(4),
            color_toner_price: parseFloat(device.rcmdPricing.rcmdColorToner).toFixed(4),
            service_cost: parseFloat(device.rcmdPricing.rcmdService).toFixed(4),
            recommended_cost_per_cartridge_color: (isDef(device.recommended_cost_per_cartridge_color) && device.recommended_cost_per_cartridge_color) || 0,
            recommended_cost_per_cartridge_mono: (isDef(device.recommended_cost_per_cartridge_mono) && device.recommended_cost_per_cartridge_mono) || 0
        }
    }
    
    const net_details = device.device_net_details.printer_costs;
    const printer_details = device.device_net_details.printer_details;
    const purchase_product = net_details.length > 1 ? net_details.filter((item) => (item.product_id.trim() === device.mfg_model_number.trim()))[0] : net_details[0]
    
    const outCost = parseFloat(purchase_product.outCost).toFixed(4);
    const msrp = parseFloat(purchase_product.msrp).toFixed(4);
    const carePackCost = parseFloat(purchase_product.carePackCost).toFixed(4);
    const estimatedCommission = parseFloat(proposed_non_network_service.estimated_commission).toFixed(2);
    const proposed_cost = device.price.replace('$','')
    const params = new URLSearchParams();
    params.append('proposed_service',JSON.stringify(proposed_non_network_service))
    params.append('proposed_purchase',JSON.stringify({
        buy_or_lease: 'buy',
        // proposed_cost: getProposedCost([outCost, msrp, carePackCost,estimatedCommission]),
        proposed_cost: (!isNaN(proposed_cost) && parseFloat(proposed_cost).toFixed(2)) || 0,
        number_printers_purchased: specs.quantity,
        duty_cycle: printer_details.duty_cycle,
        long_model: purchase_product.model_name,
        out_cost: outCost,
        msrp_cost: msrp,
        care_pack_cost: carePackCost,
        estimated_commission: estimatedCommission,
    }))
    
    const addDevice = await axios.post(window.location.origin + '/proposal/addNetworkDevice/' + proposal_id + '/', params, { 
        headers: { 
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken }
    })
    
    
    return addDevice;
};

export const getNetworkDeviceDetails = async (device, proposal) => {
    const csrftoken = getCookie('csrftoken');

    const data = {
        device_id: device.printer_id,
        proposal_id: proposal
    };

    const params = new URLSearchParams();

    for(let key in data) {
        params.append(key, data[key]);
    };
    
    const details = await axios.post(window.location.origin + '/proposal/getNetworkDeviceDetails/', params, { 
        headers: { 
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken }
        });
    
    const rcmdPricing = getRecommendedPricing(details.data);

    return Object.assign(details.data, rcmdPricing);
};

export const getNonNetworkDeviceDetails = async (device, proposal) => {
    const csrftoken = getCookie('csrftoken');
    
    const data = {
        network_device_short_name: device.short_model, 
        device_id: device.printer_id,
        proposal_id: proposal,
        mono_coverage: device.avm_mono,
        color_coverage: device.avm_color
    };
    
    const params = new URLSearchParams();

    for(let key in data) {
        params.append(key, data[key]);
    };

    
    const details = await axios.post(window.location.origin + '/proposal/getNonNetworkDeviceDetails/', params, { 
        headers: { 
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken }
        })

    return details.data;
};

export const getUpdatedProposalServiceItems = async (proposal_id) => {
    const serviceItems = await axios.get(window.location.origin + '/proposal/getUpdatedProposalServiceItems/' + proposal_id + '/');
    return serviceItems;
};

export const getPrinterCostTable = async(cost_id) => {
    const cost_table = await axios.get(window.location.origin + '/api/printer-cost/' + cost_id + '/');
    return cost_table
}