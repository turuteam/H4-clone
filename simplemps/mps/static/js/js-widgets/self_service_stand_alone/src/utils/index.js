import React from 'react';
import { pipe, assoc, isEmpty, is, difference } from 'ramda';

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