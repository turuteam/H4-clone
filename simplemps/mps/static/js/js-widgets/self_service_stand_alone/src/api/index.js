import React from 'react';
import axios from 'axios';
import { getRecommendedPricing, getProposedCost, isDef } from '../utils';
import { isEmpty, assoc, assocPath, lensProp, compose, mergeAll, flatten } from 'ramda';
import { notification } from 'antd';

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




// network printer makes
export const getMakeDetails = async () => (await axios.get(process.env.API_BASE_URL+'/proposal/getMakeDetails/').catch(error => (notification.error({
    message: error.name,
    description: error.message
}))));
export const getPrinterDetailsByMake = async (make) => (await axios.get(process.env.API_BASE_URL+'/proposal/getPrinterDetailsByMake/' + make).catch(error => (notification.error({
    message: error.name,
    description: error.message
}))));
export const getPrinterDetails = async () => (await axios.get(process.env.API_BASE_URL+'/proposal/getPrinterDetails/').catch(error => (notification.error({
    message: error.name,
    description: error.message
}))));

export const createNewProposal = async (anon) => {
    const params = new URLSearchParams();
    // could add some encryption here probably?
    
    // buymonths, dca, buysupplies
    // if(typeof anon.buymonths !== `undefined`)
    // if(typeof anon.buymonths !== `undefined`)
    // if(typeof anon.buymonths !== `undefined`)

    const data = {
        company_key: process.env.SELF_SERVICE_KEY,
        client: JSON.stringify(anon)
    }

    for(let key in data) {
        params.append(key, data[key]);
    }
    
    const newProposal = await axios.post(process.env.API_BASE_URL+'/proposal/createNewProposalSelfService/', params, { 
        headers: { 
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    }).catch(error => (notification.error({
        message: error.name,
        description: error.message
    })));
    
    return newProposal.data.proposal_id;
}

// getCompanyForExternalSource/
export const getCompanySource = async () => {
    const params = new URLSearchParams();
    // could add some encryption here probably?
    const data = {
        company_key: process.env.SELF_SERVICE_KEY,
    }

    for(let key in data) {
        params.append(key, data[key]);
    }
    
    const company = await axios.post(process.env.API_BASE_URL+'/proposal/getCompanyForExternalSource/', params, { 
        headers: { 
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    }).catch(error => (notification.error({
        message: error.name,
        description: error.message
    })));
    
    return JSON.parse(company.data.company)[0];
}

export const getNetworkDeviceDetails = async (device, proposal) => {

    const data = {
        device_id: device,
        proposal_id: proposal
    };

    const params = new URLSearchParams();
    params.append('company_key',process.env.SELF_SERVICE_KEY);
    for(let key in data) {
        params.append(key, data[key]);
    };
    
    const ppc_pricing = await axios.get(process.env.API_BASE_URL+ '/api/self-service-ppc/' + proposal + '/' + device + '/', { 
        headers: { 
            'Content-Type': 'application/x-www-form-urlencoded',
            }
    }).catch(error => (notification.error({
        message: error.name,
        description: error.message
    })));
    
    const details = await axios.post(process.env.API_BASE_URL+ '/proposal/getNetworkDeviceDetails/', params, { 
        headers: { 
            'Content-Type': 'application/x-www-form-urlencoded',
            }
        }).catch(error => (notification.error({
            message: error.name,
            description: error.message
        })));
    
    const rcmdPricing = getRecommendedPricing(details.data);
    const dets = mergeAll([details.data, rcmdPricing, ppc_pricing.data])
    
    return dets;
};

export const addNetworkDevice = async (purchase_specs, variants, proposal_id) => {
    let proposed_non_network_service = {};
    const params = new URLSearchParams();

    const specs = {
        purchased_items: purchase_specs,
        variants: flatten(variants)
    }
    
    proposed_non_network_service = {
        proposed_service: specs
    }
    
    params.append('proposed_service',JSON.stringify(proposed_non_network_service))
    
    const addDevice = await axios.post(process.env.API_BASE_URL+ '/api/self-service/addNetworkDeviceSelfService/' + proposal_id + '/', params, { 
        headers: { 
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    }).catch(error => (notification.error({
        message: error.name,
        description: error.message
    })));
      
    return addDevice;
};
