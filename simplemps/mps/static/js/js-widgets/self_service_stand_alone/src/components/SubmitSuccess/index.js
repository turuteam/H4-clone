import React, { useEffect, useContext } from 'react';
import Create_DCA from '../SelectionReview/CreateDCA';
import AppContext from '../../store/provider';
import Button from '@material-ui/core/Button';
import ClearIcon from '@material-ui/icons/Clear';
export const SubmitSuccess = () => {
    const app_context = useContext(AppContext);

    useEffect(() => {
        // component did mount
        
        return () => {
            //component will unmount
        }
    });

    return (
        <div className="success-page">
            <br/>
            <br/>
            <h1>Thank you for your Agreeing to Purchase Supplies From Us.</h1>
            <br/>
            <h3>Please Take a Few Minutes to Install the DCA By Clicking The
            Link Below</h3>
            <h3>This Will Allow Us to Refill Your Supplies Automatically</h3>
            <br/>
            <div className="d-flex justify-content-around">
                <Create_DCA />
                {/* <Button variant="outlined" color="secondary" ><ClearIcon color="secondary" fontSize="large" /> Close</Button> */}
            </div> 
            <br/>
            <br/>
        </div>
    )
}