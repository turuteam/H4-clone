import React, { useReducer, useEffect } from 'react';
import { useHistory } from "react-router-dom";
import { fromPairs, forEachObjIndexed, flatten } from 'ramda';
import { AppReducer } from './reducer';
import { 
    addNetworkDevice,
    getMakeDetails, 
    getPrinterDetails, 
    getPrinterDetailsByMake, 
    createNewProposal, 
    getCompanySource, 
    getNetworkDeviceDetails } from '../api';
import { 
    LOADMAKEDETAILS, 
    LOADPRINTERDETAILS, 
    CREATENEWPROPOSAL, 
    GETCOMPANYSOURCEDATA, 
    DEVICEDETAILS, 
    RESETDEVICEDETAILS, 
    SENDPROPOSEDPURCHASE, 
    SELECTEDVARIANT,
    RESET} from './action/action_types';

const defaultState = {
    makeOpts: [],
    shortOpts: [],
    variants: [],
    proposal: null,
    company: null,
    details: null,
    recordIdx: 0,
    purchased: [],
    loadMakeDetails: () => { },
    loadPrinterDetails: () => { },
    updatePrinterOptions: () => { },
    getDeviceDetails: () => { },
    resetDeviceDetails: () => { },
    sendProposedPurchase: () => { },
    selectVariant: () => { },
    systemReset: () => { },
    getCompany: () => { },
    createNewProposal: () => { },
}

const AppContext = React.createContext(defaultState);

export const AppProvider = (props) => {
    const { children } = props;
    const [state, dispatch] = useReducer(AppReducer, defaultState);
    const history = useHistory();

    const loadMakeDetails = async () => {
        const makes = await getMakeDetails();
        const tojson = JSON.parse(makes.data);
        const pairs = fromPairs(tojson.makes);

        let opts = []
        const buildOpts = (k, v) => (opts.push({ name: k, value: v }))
        forEachObjIndexed(buildOpts, pairs)
        dispatch({ type: LOADMAKEDETAILS, payload: opts });
    }
    
    const loadPrinterDetails = async () => {
        const printers = await getPrinterDetails();
        const tojson = JSON.parse(printers.data);
        const pairs = fromPairs(tojson.printers);

        let opts = []
        const buildOpts = (k, v) => (opts.push({ name: k, value: v }))
        forEachObjIndexed(buildOpts, pairs)
        dispatch({ type: LOADPRINTERDETAILS, payload: opts });
    }

    const updatePrinterOptions = async (make) => {
        const printers = await getPrinterDetailsByMake(make);
        const tojson = JSON.parse(printers.data);
        const pairs = fromPairs(tojson.printers);

        let opts = []
        const buildOpts = (k, v) => (opts.push({ name: k, value: v }))
        forEachObjIndexed(buildOpts, pairs)
        dispatch({ type: LOADPRINTERDETAILS, payload: opts });
    }

    const createProposal = async (client) => {
        const proposal = await createNewProposal( client, state.representative);
        dispatch({ type: CREATENEWPROPOSAL, payload: proposal });
    }

    const getDeviceDetails = async (device_id, proposal_id) => {
        const details = await getNetworkDeviceDetails(device_id, proposal_id);
        dispatch({ type: DEVICEDETAILS, payload: { ...details, device: device_id } });
    }

    const resetDeviceDetails = () => {dispatch({ type: RESETDEVICEDETAILS, payload: { reset: null, idx: state.recordIdx + 1 }})};

    const getCompany = async () => {
        const company = await getCompanySource();
        dispatch({ type: GETCOMPANYSOURCEDATA, payload: company });
    }

    const systemReset = () => {dispatch({type: RESET, payload: { default: defaultState }})};

    const sendProposedPurchase = async (proposed_purchase, variants) => {
        const results = await addNetworkDevice(proposed_purchase, variants, state.proposal);
        (typeof results !== `undefined`) && history.push('/success');
        const element = document.getElementById('rev')
        element.classList.remove('active');
        element.setAttribute('disabled', 'disabled');
        
        dispatch({type: SENDPROPOSEDPURCHASE, payload: results})
    };
    
    const selectVariant = (variant) => (dispatch({type: SELECTEDVARIANT, payload: variant}))

    useEffect(() => {
        loadMakeDetails();
        loadPrinterDetails();
        getCompany();
        return () => {

        }
    }, [])

    const app_context = {
                        makeOpts: state.makeOpts,
                        shortOpts: state.shortOpts,
                        proposal: state.proposal,
                        variants: state.variants,
                        company: state.company,
                        details: state.details,
                        recordIdx: state.recordIdx,
                        loadMakeDetails,
                        loadPrinterDetails,
                        updatePrinterOptions,
                        getDeviceDetails,
                        resetDeviceDetails,
                        sendProposedPurchase,
                        selectVariant,
                        systemReset,
                        getCompany,
                        createProposal
                    }

    return (
        <AppContext.Provider value={app_context}>
            { children }
        </AppContext.Provider>
    )
}

export default AppContext;