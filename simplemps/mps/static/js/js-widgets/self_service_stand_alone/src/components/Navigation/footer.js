import React from 'react';
import '../css/Layout.css';

export class Footer extends React.Component {
    
    render() {
        return (    
            <div className="text-light bg-dark" id="footer">©{(new Date().getFullYear())} Copyright 
                <a href="https://www.h4software.net/" style={{color: 'white'}}> H4 Software</a>
            </div>
        )
    }
}