import React from 'react';
import ReactDOM from 'react-dom';
import { Adjuster } from './components/Adjuster';
import ServiceOverview from './components/ServicerOverview';
import { getUpdatedProposalServiceItems } from '../api';
import { setItemsInLocalStorage, clearLocalStorage, getItemsInLocalStorage, syncLocalStore } from '../src/utilities';
import { isEmpty, differenceWith, includes, equals } from 'ramda';

import './index.css';
/**
 * Async run to render our element.
 */
async function run() {
    // pull the filtered data from the component root.
    const el = await document.getElementById('self-service-viewer');
    const results = JSON.parse(el.getAttribute('data-results'));
    const proposal_id = results.proposal_details.proposal.id;

    const service_items = await getUpdatedProposalServiceItems(proposal_id);
    
    if(!isEmpty(service_items)) {

        const arr = service_items.data;
        // need to sync with backend.
        const items = getItemsInLocalStorage();

        const cmp = (x, y) => {
            if(equals(x.id,y.id)) {
                return x;
            }
        };
        
        const diff = differenceWith(cmp, items, arr);
        const synced = items.filter(item => !includes(item,diff))
        
        syncLocalStore(synced);

        //  enable step review if there are items in storage.
        const stepReview = document.getElementById('step-review');
        if(stepReview.classList.contains('disabled')) {
            stepReview.classList.remove('disabled');
            stepReview.parentNode.classList.add('is-active');
        }

    } else {
        clearLocalStorage();
    }
        

    // render the adjuster
    ReactDOM.render(<ServiceOverview results={results} />, document.getElementById('self-service-viewer'));
}

run();