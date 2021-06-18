import React from 'react';
import { pipe, assoc, isEmpty, is, difference } from 'ramda';
/**
 * Save device to local storage.
 * 
 * @param {array} items 
 */
export const bulkUpdateItemsInLocalStorage = (device) => {
    const storage = getItemsInLocalStorage();
    const storage_payload = storage.filter( item => (item.mfg_model_number !== device.mfg_model_number));
    localStorage.setItem('mps_self_service', JSON.stringify(storage_payload));

    return;
};
export const setItemsInLocalStorage = (item) => {
    let current_saved = getItemsInLocalStorage();

    if(is(Array, item))
        return;

    current_saved.push(item);
    localStorage.setItem('mps_self_service', JSON.stringify(current_saved));

    return;
};
export const syncLocalStore = (items) => (localStorage.setItem('mps_self_service', JSON.stringify(items)))
/**
 * Retrieve devices saved in local storage.
 */
export const getItemsInLocalStorage = () => (JSON.parse(localStorage.getItem('mps_self_service') || "[]"));
/**
 * Clear all items from mps saved in local storage.
 */
export const clearLocalStorage = () => (localStorage.removeItem('mps_self_service'));
/**
 * Check if this printer needs updated instead of saving the device.
 * 
 * @param {object} item 
 */
export const checkUpdate = (item) => {
    const storage = getItemsInLocalStorage();
    if(!isEmpty(storage)) {
        return storage.some(saved_item => (saved_item.mfg_model_number === item.mfg_model_number));
    } 
    return false;
}

export const getItemFromLocalStorage = (device) => {
    const storage = getItemsInLocalStorage();
    if(!isEmpty(storage))  { 
        const storageItem = storage.filter( item => (item.mfg_model_number === device.mfg_model_number))
        return storageItem[0];
    }

    return false;
}
/**
 * set avm page results for printer item.
 * 
 * @param result
 * @param details 
 */
export const updateAvm = (result, details) => {
    return pipe(assoc('avm_color', details.avm_color) , assoc('avm_mono', details.avm_mono))(result)
}
/**
 * 
 * @param {*} result 
 * @param {*} details 
 */
export const updateRcmd = (pricing, item) => (assoc('rcmdPricing', pricing, item));
/**
 * 
 * @param {*} details 
 * @param {*} item 
 */
export const updatePageCostDetails = (details, item) => (assoc('page_details', details, item))
/**
 * 
 * @param {*} details 
 * @param {*} item 
 */
export const updatePrinterCosts = (details, item) => (assoc('printer_costs', details, item))
/**
 * Associate the current device result details and non-network details.
 * 
 * @param {object} result 
 * @param {object} details 
 */
export const associateNonNetworkProperties = (result, details) => (assoc('is_non_network', details)(result))

// running calculations with network details.
export const getRecommendMonoTonerPrice = (scaledTonerCPP, pages, monoCoverage) => (+(pages * (scaledTonerCPP * (monoCoverage / 0.05))).toFixed(4))
export const getRecommendColorTonerPrice = (colorTonerMarginPrice, totalMonthlyColorPages, colorCoverage) => (+(colorTonerMarginPrice * totalMonthlyColorPages * colorCoverage / 0.05).toFixed(4))
export const getRecommendServicePrice = (serviceBumpedMarginPrice, totalMonthlyPages) => (+(serviceBumpedMarginPrice * totalMonthlyPages).toFixed(4))
export const getRecommendMonoSalesPrice = (monoTonerPrice, servicePrice, monoPages, colorPages) => (+((monoTonerPrice + (servicePrice * monoPages / (monoPages + colorPages))) / monoPages).toFixed(4))
export const getRecommendColorSalesPrice = (colorTonerPrice, servicePrice, monoPages, colorPages) => (+((colorTonerPrice + (servicePrice * colorPages / (monoPages + colorPages))) / colorPages).toFixed(4))

export const getRecommendedPricing = (details, specs=null) => {
    
    const toner_costs = !specs ? details.toners_costs : details.rcmdPricing.toner_costs;
    const device = !specs ? details.printer_details : details;

    const numPagesColor = !specs ? device.avm_color : (specs.color * specs.quantity)
    const numPagesMono = !specs ? device.avm_mono : (specs.mono * specs.quantity)

    const rcmdMonoToner = getRecommendMonoTonerPrice(toner_costs.scaled_mono_cost, numPagesMono, 0.05) || 0;
    const rcmdColorToner = getRecommendColorTonerPrice(toner_costs.scaled_color_cost, numPagesColor, 0.05) || 0;
    
    const totalPages = numPagesColor + numPagesMono;
    let rcmdService = getRecommendServicePrice(toner_costs.scaled_service_cost, totalPages) || 0;

    const sf_mono_price = getRecommendMonoSalesPrice(rcmdMonoToner, rcmdService, numPagesMono, numPagesColor) || 0;
    const sf_color_price = getRecommendColorSalesPrice(rcmdColorToner, rcmdService, numPagesMono, numPagesColor) || 0;

    return {
        rcmdPricing: {
            toner_costs: toner_costs,
            rcmdMonoToner: rcmdMonoToner,
            rcmdColorToner: rcmdColorToner,
            totalPages: totalPages,
            rcmdService: rcmdService,
            sf_mono_price: sf_mono_price,
            sf_color_price: sf_color_price
        }
    }
}

export const getProposedCost = (calcs) => ( calcs.reduce((a, b) => (parseFloat(a) + parseFloat(b))).toFixed(2));
export const isDef = (val) => (typeof val !== 'undefined')