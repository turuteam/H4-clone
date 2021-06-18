import React from 'react';
import { Navigator } from '../Navigation';
import { Footer } from '../Navigation/footer';
import { Container } from 'react-bootstrap';
import background from '../../images/imageOne.png';
import { Crumbs } from '../BreadCrumbs';
import '../css/Layout.css';
export class Layout extends React.Component {
    constructor(props) {
        super(props)
    }

    render() {

        let { children } = this.props;
        return (
            <>
                <Navigator links={['Proposal Info', 'Review Selections', 'Test']} />
                <img src={background} style={{zIndex: '-1', position:'relative'}} height={'300px'} width={'100%'}/>
                <div className="layout">     
                    <br/>        
                    <Container>
                        { children }
                    </Container>
                    <br/>
                </div>
                <Footer />
            </>
        )
    }
}