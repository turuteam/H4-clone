var userID = 0;
function editUser(userID){
    var div = document.getElementById(userID);
    div.style.display = "block";
}


function closeDiv(userID){
    var div = document.getElementById(userID);
    div.style.display = "none";
}

function updateDiv(userID){

    //console.log($('#'+userID+' #userFirstName').val());

    $.ajax({
        url: '/manageReps/update',
        method: 'POST',
         
        data: {
            "userID" : userID,
            "userFirstName" : $('#'+userID+' #userFirstName').val(),
            "userLastName" : $('#'+userID+' #userLastName').val(),
            "userNumber" : $('#'+userID+' #userNumber').val(),
            "userEmail" : $('#'+userID+' #userEmail').val(),
            'csrfmiddlewaretoken' : $("input[name=csrfmiddlewaretoken]").val(),
        },
        
        success: function(data){
            alert("successfully submitted!");
            window.location.reload();
        }, 
        error: function(error,data){
            console.log(data);
            console.log(error)
            console.log("error")
            alert(error)
        }
	});
}

function deleteReps(userID){
    if (confirm('Are you sure you want to delete this representative?')) {
        $.ajax({
            url: '/manageReps/delete',
            method: 'POST',
             
            data: {
                "userID" : userID,
                'csrfmiddlewaretoken' : $("input[name=csrfmiddlewaretoken]").val(),
            },
            
            success: function(data){
                alert("successfully deleted!");
                window.location.reload();
            }, 
            error: function(error,data){
                console.log(data);
                console.log(error)
                console.log("error")
                alert(error)
            }
        });
    } else {
        closeDiv(userID);
    }
}