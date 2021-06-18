import React from 'react';
import Button from '@material-ui/core/Button';
import EmailIcon from '@material-ui/icons/Email';

import { makeStyles, Theme, createStyles } from '@material-ui/core/styles';
import Modal from '@material-ui/core/Modal';
import Backdrop from '@material-ui/core/Backdrop';
import Fade from '@material-ui/core/Fade';
import { ContactForm } from '../ContactForm';
import '../css/Layout.css';

export const Contact = (props) =>  {

    const useStyles = makeStyles((theme) =>
    createStyles({
        modal: {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
        },
        paper: {
            backgroundColor: theme.palette.background.paper,
            color: 'black',
            border: '2px solid #000',
            boxShadow: theme.shadows[5],
            padding: theme.spacing(2, 4, 3),
        },
        }),
    );
    
    const classes = useStyles();
    const [open, setOpen] = React.useState(false);
    
    const handleOpen = () => {
        setOpen(true);
    };
    
    const handleClose = () => {
        setOpen(false);
    };
    return (
        <div className="text-center mb-2 mt-4 ">
            <Button variant="outlined" color="secondary" id="mailImage" onClick={handleOpen}><EmailIcon color="secondary" fontSize="large" id="mailImage"/> Contact</Button>
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
                    <div className={classes.paper}>
                        <h2 id="transition-modal-title" style={{textAlign: 'center'}}>Contact</h2>
                        {/* <p id="transition-modal-description">react-transition-group animates me.</p> */}
                        <ContactForm />
                    </div>
                </Fade>
            </Modal>
        </div>
    )
}