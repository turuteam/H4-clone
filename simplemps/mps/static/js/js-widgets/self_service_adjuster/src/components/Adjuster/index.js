import React from 'react';
import Modal from 'react-modal';
import { ServiceViewer } from '../ServiceViewer';
import Paper from '@material-ui/core/Paper';
import Grid from '@material-ui/core/Grid';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Button from '@material-ui/core/Button';
import SaveIcon from '@material-ui/icons/Save';
import DeleteIcon from '@material-ui/icons/Delete';
import Checkbox from '@material-ui/core/Checkbox';
import FormGroup from '@material-ui/core/FormGroup';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import FormControl from '@material-ui/core/FormControl';

import { 
    CssTextField,
    createData,
    useStyles
} from '../../utilities/material';
import { updateAvm, setItemsInLocalStorage, checkUpdate, associateNonNetworkProperties, updateRcmd, updatePageCostDetails, getRecommendedPricing, isDef, getItemFromLocalStorage, bulkUpdateItemsInLocalStorage, getItemsInLocalStorage } from '../../utilities';
import { addNetworkDevice, getNonNetworkDeviceDetails, getUpdatedProposalServiceItems, removeNetworkDevice } from '../../../api';
import { forEachObjIndexed, isEmpty, set, lens, prop, assoc, last, mergeRight, mergeAll } from 'ramda';

const customStyles = {
    content: {
        background: '#FFEBCD',
        top:'50%',
        left:'50%',
        right:'auto',
        bottom:'auto',
        marginRight:'-50%',
        transform:'translate(-50%,-50%)',
        boxShadow: '10px 10px 5px grey',
        maxWidth: '800px',
    }
};


Modal.setAppElement('#self-service-viewer')
/**
 * Adjuster component to provide filter viewing and more options for the item selected.
 * 
 * @param {object} props 
 */
export const Adjuster = (props) => {

    const [modalIsOpen, setIsOpen] = React.useState(false);
    const [result, setResult] = React.useState(false);
    // default non-network
    // const [is_network, setNetwork] = React.useState(false);
    
    // default network, always network device.
    const [is_network, setNetwork] = React.useState(true);

    /**
     * Update selected item state, open the modal.
     * 
     * @param {event} e 
     */
    const openModel = async (e) => {
        let item = props.data.printers.filter( result => (result.mfg_model_number === e.target.id))[0];
        const { proposal_details } = props.data;
        const { device_net_details } = item;
        const pricing = getRecommendedPricing(item.device_net_details);

        const { 
            printer_details, 
            page_cost_details, 
        } = device_net_details;
        
        // we need to show the avm stats with the result
        item = updateAvm(item, printer_details);

        // we need the page cost info.
        item = updatePageCostDetails(page_cost_details,item);

        // if we set to non network search then we need to make another api call to get the details, this is not being used for now.
        if(!is_network) {
            const NonNetworkDetails = await getNonNetworkDeviceDetails(item, proposal_details.proposal.id)
            item = associateNonNetworkProperties(item, NonNetworkDetails)
        }

        // recommended pricing data is calculated from the api, add the recommended calculations
        // for this proposal item.
        const result = updateRcmd(pricing.rcmdPricing, item);
        
        updateStateResult(result)
        setIsOpen(true);
    };
    /**
     * Save the selected device from the viewer modal, to purchased items.
     */
    const saveDevice = async () => {
        const { proposal_details } = props.data;
        const id = proposal_details.proposal.id;

        const form = document.getElementById('form-specs');
        const specs = Object.values(form).reduce((obj,field) => { obj[field.name] = field.value; return obj }, {})
        const isSaved = checkUpdate(result);
        let res = {};
        
        if(!isSaved) {
            
            res = await addNetworkDevice(result, specs, id, is_network);
            if(res.status === 200 && typeof res.data.service_item_id !== 'undefined') {
                const items = await getUpdatedProposalServiceItems(id);
                const recent_save = last(items.data);
                const saved_result = [ 'mfg_model_number', 'purchase_heading', 'new_purchase_specification'].map((key) => (mergeRight(recent_save,{ [`${key}`] : result[`${key}`] })))
                
                setItemsInLocalStorage(mergeAll(saved_result));
            }
        } else {
            const stored_item = getItemFromLocalStorage(result);
            
            // add the new device with updated calculations.
            res = await addNetworkDevice(result, specs, id, is_network);
            const service_item_id = res.data.service_item_id

            if(res.status === 200 && typeof service_item_id !== 'undefined') { 

                const removed = await removeNetworkDevice(stored_item.id, id);

                // if there is an error from the backend remove the new device, maintain state.
                if(removed.status !== 200) {
                    await removeNetworkDevice(service_item_id, id)
                    return;
                }
                // update the local storage to reflect backend data.
                bulkUpdateItemsInLocalStorage(result);

                const items = await getUpdatedProposalServiceItems(id);
                const recent_save = last(items.data);
                const saved_result = [ 'mfg_model_number', 'purchase_heading', 'new_purchase_specification'].map((key) => (mergeRight(recent_save,{ [`${key}`] : result[`${key}`] })))
                
                setItemsInLocalStorage(mergeAll(saved_result));
            } 
        }
        
        // enable the next step.
        if(res.status === 200 && typeof res.data.service_item_id !== 'undefined') {
            const stepReview = document.getElementById('step-review');
            if(stepReview.classList.contains('disabled')) {
                stepReview.classList.remove('disabled');
                stepReview.parentNode.classList.add('is-active');
            }

        }

        setIsOpen(false)
       
    }
    /**
     * Update recommended pricing values on input change.
     */
    const setRecommendedPricing = () => {
        const form = document.getElementById('form-specs');
        const specs = Object.values(form).reduce((obj,field) => { obj[field.name] = field.value; return obj }, {})
        // don't send empty values to the backend
        const setDefaults = (value, key) => { 
            if(isEmpty(value)) {
                switch(key) {
                    case 'mono':
                    case 'color':
                        value = '0'
                        break;
                    default:
                        value = '1'
                        break;
                }

                specs[`${key}`] = value;
            }
        }

        forEachObjIndexed(setDefaults, specs);
    
        const newPrice = getRecommendedPricing(result, specs);

        const rcmdPricingLens = lens(prop('rcmdPricing'), assoc('rcmdPricing'));
        const item = set(rcmdPricingLens, newPrice.rcmdPricing, result);

        updateStateResult(item);
    }
    /**
     * close opened state modal.
     */
    const closeModel = () => (setIsOpen(false));
    const updateStateResult = React.useCallback((item) => (setResult(item)), []);
    const handleChange = (e) => (setNetwork(e.target.checked));

    const classes = useStyles();
    
    const cpp_mono = (isDef(result.rcmdPricing) &&  result.rcmdPricing.sf_mono_price) || 0;
    const cpp_color = (isDef(result.rcmdPricing) && result.rcmdPricing.sf_color_price) || 0;
    
    const ppc_mono = (isDef(result.recommended_mono_ppc) && result.recommended_mono_ppc) || 0;
    const ppc_color = (isDef(result.recommended_color_ppc) && result.recommended_color_ppc) || 0;

    const totalSavings = (((((cpp_mono * 1) * (result.avm_mono)) + ((cpp_color * 1) * (result.avm_color))) * 0.28) * 12).toFixed(2);

    const rows = [
        createData('Price', result.price),
        props.data.is_cpp === 'cpp' ? createData('CPP Mono', cpp_mono ) : createData('Mono Toner Price', ppc_mono),
        props.data.is_cpp === 'cpp' ? createData('CPP Color', cpp_color ) : createData('Color Toner Price', ppc_color),
    ];

    return (
        <div>
            <ServiceViewer data={props.data.printers} is_cpp={props.data.is_cpp} modalcontrol={openModel} item_review={props.overview} />
            {/* <FormControl component="fieldset">
                <FormGroup aria-label="position" row>
                <FormControlLabel
                    value="is_network"
                    control={<Checkbox color="primary" defaultChecked inputProps={{ 'aria-label': 'secondary checkbox' }} name="is_network" onChange={handleChange} />}
                    label="Network Device"
                    labelPlacement="start"
                    />
                </FormGroup> 
            </FormControl> */}
                                    
            <Modal
                isOpen={modalIsOpen}
                onRequestClose={closeModel}
                style={customStyles}
                contentLabel="Self-Service Modal"
                overlayClassName="Overlay"
            >
                <div className={classes.root}>
                    <Grid container spacing={3}>
                        <Grid item xs={12}>
                            <Paper className={classes.paper}>
                                <div>
                                    <h4 >{result.purchase_heading}</h4>
                                    <p style={{ 
                                        fontSize: '.87rem', 
                                        color: 'grey',margin: 'auto', 
                                        paddingBottom: '25px'}}>
                                        {result.new_purchase_specification}
                                    </p>
                                    <div style={{ 
                                        backgroundColor: '#37d67a',
                                        borderRadius: '5px',
                                    }}>
                                        <p style={{ 
                                        fontSize: '1.25rem', 
                                        color: 'white',
                                        margin: 'auto',
                                        fontWeight: 'bold',}}>
                                        YOUR ANNUAL SAVINGS 
                                        </p>
                                        <p style={{ 
                                        fontSize: '0.90rem', 
                                        color: 'white',
                                        margin: 'auto',
                                        fontWeight: 'bold',}}>
                                        If You Commit To Purchase Supplies And/Or Service From Us
                                        </p>
                                        <p style={{ 
                                        fontSize: '1.25rem', 
                                        color: 'white',
                                        margin: 'auto',
                                        fontWeight: 'bold',}}>
                                        ${totalSavings}
                                        </p>
                                    </div>
                                </div>
                            </Paper>
                        </Grid>
                        <Grid item xs={12} md={6}>
                            <Paper className={classes.paper}>
                                <TableContainer component={Paper}>
                                    <Table className={classes.table} aria-label="caption table">
                                        <TableHead>
                                        <TableRow>
                                            <TableCell><span>Purchase and Operation Costs</span></TableCell>
                                            <TableCell align="right"></TableCell>
                                        </TableRow>
                                        </TableHead>
                                        <TableBody >
                                        {rows.map((row) => (
                                            <TableRow key={row.name}>
                                            <TableCell component="th" scope="row">
                                                {row.name}
                                            </TableCell>
                                            <TableCell align="right">{row.value}</TableCell>
                                            </TableRow>
                                        ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            </Paper>
                        </Grid>
                        <Grid item sm={12} md={6}>
                            <Paper className={classes.paper}>
                                        <span><b>Expected Print Volume for Each Device</b></span>
                                <form className={classes.root} noValidate id="form-specs" onChange={(e) => (setRecommendedPricing(e))}>
                                    <CssTextField className={classes.margin} id="mono" label="Avg Mono Pages/Month" name="mono" {...(typeof result.avm_mono !== 'undefined' ? {defaultValue:result.avm_mono} : {})} />
                                    <CssTextField className={classes.margin} id="color" label="Avg Color Pages/Month" name="color" {...(typeof result.avm_color !== 'undefined' ? {defaultValue:result.avm_color} : {})} />
                                    <CssTextField className={classes.margin} id="quantity" label="Number of Devices Needed" name="quantity" defaultValue={1} />
                                </form>
                            </Paper>
                        </Grid>
                        <Grid item xs={6}>
                            <Button
                                variant="contained"
                                color="secondary"
                                size="large"
                                className={classes.button}
                                startIcon={<DeleteIcon />}
                                onClick={closeModel}
                            >
                                Back
                            </Button>
                        </Grid>
                        
                        <Grid item xs={6}>
                            <Button
                                variant="contained"
                                color="primary"
                                size="large"
                                className={classes.button}
                                startIcon={<SaveIcon />}
                                style={{float: 'right'}}
                                onClick={saveDevice}
                            >
                                Save
                            </Button>
                        </Grid>
                    </Grid>
                </div>
            </Modal>
        </div>
    )
}