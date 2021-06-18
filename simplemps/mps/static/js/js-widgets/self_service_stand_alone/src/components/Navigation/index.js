import React from 'react';
import { Link } from 'react-router-dom';
import { Navbar, NavDropdown, Nav, Form, FormControl, Button } from 'react-bootstrap'; 
import AppContext from '../../store/provider';
import { Contact } from '../Contact';
import { isEmpty, isNil } from 'ramda';

export class Navigator extends React.Component {
    constructor(props) {
        super(props)
    }

    render() {
        return (
            <AppContext.Consumer>
            {
                ({ purchased, proposal, company }) => {
                    return (
                        <Navbar collapseOnSelect expand="lg" bg="dark" variant="dark">
                            <Navbar.Brand as={Link} to="/company">{(!isNil(company)) ? company.fields.name: 'Company Logo'}</Navbar.Brand>
                            <Navbar.Toggle aria-controls="responsive-navbar-nav" />
                            <Navbar.Collapse id="responsive-navbar-nav">
                                <Nav className="mr-auto"  defaultActiveKey="/" >
                                    <Nav.Link as={Link} id="start" to="/" eventKey="/" disabled={!isNil(proposal)}>Proposal Info</Nav.Link>
                                    <Nav.Link as={Link} id="rev" to="/selection-review" eventKey="/selection-review" disabled={isNil(proposal) && !isEmpty(purchased)}>Selection Review</Nav.Link>
                                </Nav>
                                <Nav>
                                    <Contact/>
                                </Nav>
                            </Navbar.Collapse>
                        </Navbar>
                    )
                }
            }
            </AppContext.Consumer>
            
        )
    }
}