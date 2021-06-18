import React from 'react';
import {checkUpdate, getRecommendedPricing, isDef} from '../../utilities';
import {makeStyles} from '@material-ui/core/styles';
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
import Modal from '@material-ui/core/Modal';
import Backdrop from '@material-ui/core/Backdrop';
import Fade from '@material-ui/core/Fade';

const useStyles = makeStyles((theme) => ({
    root: {
        flexGrow: 1
    },
    paper: {
        padding: '3%',
        height: 250,
        width: 'auto'
    },
    control: {
        padding: theme.spacing(2)
    },
    row_margin: {
        marginBottom: '1rem'
    },
    image: {
        width: '300px',
        height: '200px'
    },
    modal: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      },
      paper_image: {
        backgroundColor: theme.palette.background.paper,
        border: '2px solid #000',
        boxShadow: theme.shadows[5],
        padding: theme.spacing(2, 4, 3),
      },
}));

/**
 * Display filtered items for review.
 *
 * @param {object} props
 */
export const ServiceViewer = (props) => {
    const [spacing,
        setSpacing] = React.useState(2);
    const classes = useStyles();
    const {item_review, is_cpp} = props;

    return (props.data.map((result, key) => {
        const isMatched = checkUpdate(result);
        const {printer_details} = result.device_net_details;

        const pricing = getRecommendedPricing(result.device_net_details);
        const ppc_mono = (isDef(result.recommended_mono_ppc) && `$${result.recommended_mono_ppc}`) || null;
        const ppc_color = (isDef(result.recommended_color_ppc) && `$${result.recommended_color_ppc}`) || null;

        const mono = is_cpp === 'cpp'
            ? {
                name: 'CPP Mono',
                value: '$' + pricing.rcmdPricing.sf_mono_price
            }
            : {
                name: 'Mono Toner Price',
                value: ppc_mono
            }
        const color = is_cpp === 'cpp'
            ? {
                name: 'CPP Color',
                value: '$' + pricing.rcmdPricing.sf_color_price
            }
            : {
                name: 'Color Toner Price',
                value: ppc_color
            }

        // implement modal image overlay
        const [open, setOpen] = React.useState(false);

        const handleOpen = () => {
            setOpen(true);
          };
        
          const handleClose = () => {
            setOpen(false);
          };

        return !item_review
            ? <div
                    style={{
                    border: '1px solid',
                    margin: '1%',
                    padding: '2%'
                }}
                    key={key}>
                    <Grid container className={classes.root} >
                        <Grid className={classes.row_margin} item xs={12} >
                            <strong>{result.purchase_heading}</strong>
                        </Grid>
                        <Grid container direction="row" justify="space-between" alignItems="center">
                            {/* <Grid item ><img src="https://via.placeholder.com/300x200" /></Grid> */}
                            <Grid item xs={12} sm={6} md={4}>
                                <button type="button" onClick={handleOpen}><img className={classes.image} src={`/static/img/printers/${result.mfg_model_number}.jpg`} onError={(e) => (e.target.src='/static/img/Background-3.jpg')} /></button>
                                <Modal
                                    aria-labelledby="transition-modal-title"
                                    aria-describedby="transition-modal-description"
                                    className={classes.modal}
                                    open={open}
                                    onClose={handleClose}
                                    closeAfterTransition
                                    BackdropComponent={Backdrop}
                                    BackdropProps={{
                                    timeout: 500,
                                    }}
                                >
                                    <Fade in={open}>
                                    <div className={classes.paper_image}>
                                        <h2 style={{color: 'black', textAlign:'center'}} id="transition-modal-title">{result.short_model}</h2>
                                        <img src={`/static/img/printers/${result.mfg_model_number}.jpg`} width={500} height={500} onError={(e) => (e.target.src='/static/img/Background-3.jpg')} />
                                        <p id="transition-modal-description">{result.new_purchase_specification}</p>
                                    </div>
                                    </Fade>
                                </Modal>
                            </Grid>
                            <Grid item xs={12} sm={6} md={4}>
                                <div>
                                    {result.new_purchase_specification}
                                </div>
                            </Grid>
                            <Grid item xs={6} md={4}>
                                <div>
                                    <strong style={{padding: '50px'}}>{!result.isOwned ? 'Price: ' + result.price : result.is_color_device ? 'Color' : 'Mono'}</strong>
                                    <div id="item-select" ><button id={result.mfg_model_number} className="cell button mps-green" type="button" onClick={(e) => props.modalcontrol(e)} >{ !isMatched ? 'Select' : 'Update'}</button></div>
                                </div>
                            </Grid>
                        </Grid>
                    </Grid>
                </div>
            : <div
                style={{
                border: '1px solid',
                margin: '1%',
                padding: '2%',
                backgroundColor: 'rgb(255, 235, 205)'
            }}
                key={key}>
                <Grid container className={classes.root} spacing={1}>
                    <Grid item xs={12} md={4}>
                        <Paper className={classes.paper}>
                            <strong>{result.purchase_heading}</strong>
                            <br/>
                            <br/> {result.new_purchase_specification}
                        </Paper>
                    </Grid>
                    <Grid item xs={12} md={4}>
                        <Paper className={classes.paper}>
                            <Table >
                                <TableHead>
                                    <TableRow>
                                        <TableCell align="center">
                                            <span>
                                                <b>Purchase and Operation Costs</b>
                                            </span>
                                        </TableCell>
                                        <TableCell/>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {[
                                        {
                                            name: 'Price',
                                            value: result.price
                                        },
                                        mono,
                                        color
                                    ].map((row) => (
                                        <TableRow key={row.name}>
                                            <TableCell component="th" scope="row">
                                                {row.name}
                                            </TableCell>
                                            <TableCell align="right">
                                                {row.value}
                                            </TableCell>
                                        </TableRow>
                                    ))
}
                                </TableBody>
                            </Table>
                        </Paper>
                    </Grid>
                    <Grid item xs={12} md={4}>
                        <Paper className={classes.paper}>
                            <Table >
                                <TableHead>
                                    <TableRow>
                                        <TableCell align="center">
                                            <span>
                                                <b>Expected Print Volume for Each Device</b>
                                            </span><br/>
                                        </TableCell>
                                        <TableCell/>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {/* {name: 'Quantity', value: result.quantity} */}
                                    {[
                                        {
                                            name: 'AVM Mono',
                                            value: printer_details.avm_mono
                                        }, {
                                            name: 'AVM Color',
                                            value: printer_details.avm_color
                                        }
                                    ].map((row) => (
                                        <TableRow key={row.name}>
                                            <TableCell component="th" scope="row">
                                                {row.name}
                                            </TableCell>
                                            <TableCell align="right">
                                                {row.value}
                                            </TableCell>
                                        </TableRow>
                                    ))
}
                                </TableBody>
                            </Table>
                        </Paper>
                    </Grid>
                </Grid>
                <div
                    id="item-select"
                    style={{
                    float: 'right'
                }}>
                    <button
                        id={result.mfg_model_number}
                        className="cell button mps-green"
                        type="button"
                        onClick={(e) => props.modalcontrol(e)}>{!isMatched
                            ? 'Select'
                            : 'Update'}</button>
                </div>
                <br/>
                <br/>
            </div>
    }))
}