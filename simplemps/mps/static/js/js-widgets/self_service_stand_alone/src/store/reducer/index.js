import React from 'react';
import { LOADMAKEDETAILS, LOADPRINTERDETAILS, CREATENEWPROPOSAL, GETCOMPANYSOURCEDATA, DEVICEDETAILS, RESETDEVICEDETAILS, RESET, SELECTEDVARIANT, SENDPROPOSEDPURCHASE } from '../action/action_types';
export const AppReducer = (state, action) => {
    switch(action.type) {
        case LOADMAKEDETAILS:
            return {
                ...state,
                makeOpts: action.payload
            }
        case LOADPRINTERDETAILS:
            return {
                ...state,
                shortOpts: action.payload
            }
        case CREATENEWPROPOSAL:
            return {
                ...state,
                proposal: action.payload
            }
        case GETCOMPANYSOURCEDATA:
            return {
                ...state,
                company: action.payload
            }
        case DEVICEDETAILS:
            return {
                ...state,
                details: action.payload
            }
        case RESETDEVICEDETAILS:
            return {
                ...state,
                details: action.payload.reset,
                recordIdx: action.payload.idx
            }
        case RESET:
            return {
                ...state,
                proposal: null,
                details: null,
                variants: [],
                recordIdx: 0
            }
        case SELECTEDVARIANT:
            return {
                ...state,
                variants: [...state.variants, action.payload]
            }
        case SENDPROPOSEDPURCHASE:
            return {
                ...state,
                purchased: action.payload
            }
        default:
            return {
                ...state
            }
    }
}