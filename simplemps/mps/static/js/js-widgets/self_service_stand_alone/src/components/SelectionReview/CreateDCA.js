import React, {useState} from 'react';

const Create_DCA = () => {

    const [dcaData, setDcaData] = useState([]);
    const api_key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJvZmYiOmZhbHNlLCJpc3MiOm51bGwsInN1YiI6IkRlcyBQbGFpbmVzIE9mZmljZSBFcXVpcG1lbnQiLCJhdWQiOiI5NDQ3ZjRjMi0yNmQwLTRhNWYtYjBiZS0xNjZiNTM2ZmJiMDIiLCJpYXQiOjE0NzU2Nzk0OTksIm5iZiI6bnVsbCwiZXhwIjpudWxsfQ.bkbCljMwMO7IfEa5sC0GOFHC249Y82oFUjmKE07O4dmC8qdjD6mSWqTsd6c3evpSac06fJbWg_FOdgjAwlAvHA';
    const groupId = 'fb1bec85-4007-466f-a515-02d601eedc6c';

    const createRecord=()=>{
        fetch(`https://cors-anywhere.herokuapp.com/https://axess.axessmps.com/restapi/3.13.0/dcas`,{
            method:"PUT",
            body:JSON.stringify({"name" : "Testing", "groupId": groupId, "dcaType": "Pulse"}),
            headers: new Headers ({
                'Content-Type':'application/json',
                'x-api-key': api_key,
                'Authorization': 'Basic dGRjcnV6QGZvb3RwcmludG1wcy5jb206QmFzZWJhbGwyMDIw',
                'Accept': 'application/json'

            })
        })
        .then(res=> res.json())
        .then((json) => {
            console.log(json);
            setDcaData(json.activationPin);
            window.location.assign(`https://axess.axessmps.com/restapi/dcas/downloads/download?architecture=ECIDCAPi-Windows&buildType=ga&pin=${dcaData}`);
        });

    }

    return (
        <div>
            <button onClick={createRecord}>Install DCA</button>
        </div>
    );
        
};
        
export default Create_DCA;