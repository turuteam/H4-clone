import React from 'react';
import ReactDom from 'react-dom';
import { BrowserRouter, Switch, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { AppProvider } from './store/provider';
import { ProposalInfo } from './components/Form';
import { Company } from './components/Company';
import { SubmitSuccess } from './components/SubmitSuccess';
import EditableTable from './components/SelectionReview';

import 'bootstrap/dist/css/bootstrap.min.css';
import './index.css';

// fetch key
const key = process.env.SELF_SERVICE_KEY;

ReactDom.render(
        <BrowserRouter >
            <AppProvider>
                <Layout>
                    <Switch>
                        <Route exact path="/" >
                            <ProposalInfo company_key={key} />
                        </Route>
                        <Route path="/company" >
                            <Company />
                        </Route>
                        <Route path="/selection-review" >
                            <EditableTable />
                        </Route>
                        <Route path="/success" >
                            <SubmitSuccess />
                        </Route>
                    </Switch>
                </Layout>
            </AppProvider>
        </BrowserRouter>
    , document.getElementById('root')
);