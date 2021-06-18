import React, { useContext } from 'react';
import { Form, Button } from 'react-bootstrap';
import AppContext from '../../store/provider';
import { isEmpty, isNil } from 'ramda'
import { useHistory } from "react-router-dom";

export const ProposalInfo = () => {
    const app_context = useContext(AppContext);
    const { createProposal, company } = app_context;
    const history = useHistory();
    
    const Submit = (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        formData.append('contact', '');
        formData.append('is_supplies_only', 'True');
        formData.append('is_pricing_per_page', 'True');
        formData.append('city','london');
        formData.append('state', 'KY');
        formData.append('zipcode', '40741');
        formData.append('country', 'United States');
        formData.append('contract_service_levels', '1');
        formData.append('rep_company', '');
        
        const formDataObj = Object.fromEntries(formData.entries());
        

        if(isEmpty(formDataObj)) return;
        (typeof window !== `undefined`) && (history.push('/selection-review'));
        createProposal(formDataObj);
    }

    return <Form style={{color:'white'}} onSubmit={Submit} >
        <Form.Group controlId="formName">
            <Form.Label>Name</Form.Label>
            <Form.Control type="text" placeholder="Name" name="organization_name"/>
        </Form.Group>
        <Form.Group controlId="formEmail">
            <Form.Label>Email</Form.Label>
            <Form.Control type="email" placeholder="Email" name="email"/>
            <Form.Text className="text-muted">
                <p className="text-small text-white">We'll never share your email with anyone else.</p>
            </Form.Text>
        </Form.Group>
        
        <Form.Group controlId="formPhone">
            <Form.Label>Phone Number</Form.Label>
            <Form.Control type="telephone" placeholder="Phone Number" name="phone_number"/>
        </Form.Group>
        <Form.Group className="mt-5" controlId="formBuyMonths">
            <Form.Check type="checkbox" label={`Agree to Buy this Product from ${(!isNil(company)) ? company.fields.name : '{company_name}'} for the next 12 months.`} name="buymonths"/>
        </Form.Group>
        <Form.Group controlId="formDCA">
            <Form.Check type="checkbox" label="Agree to Add a DCA and Have Supplies Refilled Automatically." name="dca"/>
        </Form.Group>
        <Form.Group controlId="formSupplies">
            <Form.Check type="checkbox" label="Agree to Buy These Supplies When They Arrive." name="buysupplies"/>
        </Form.Group>
        <Button className="mt-5" variant="primary" type="submit" >
            Submit
        </Button>
    </Form>
}