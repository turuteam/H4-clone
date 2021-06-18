table_headers = {
  "network" : [
    "Equipment",
    "#Devices",
    "Monthly Mono Pages",
    "Monthly Color Pages",
    "Base Volume Mono",
    "Base Rate",
    "Base Volume Color",
    "Base Rate",
    "Propose Mono Price",
    "Proposed Color Price",
    "Equipment Purchase",
    "Equipment Price",
    "",
  ]
}





$(document).ready(function () {
  showNetworkTable();
});

function showNetworkTable() {
  var data = [] //load the data through ajax eventually
  data.push(table_headers.network)
  var container = document.getElementById('p-service');

  var hot = new Handsontable(container, {
    data: data,
    rowHeaders: false,
    colHeaders: false,
    filters: true,
    dropdownMenu: true
  });
  
  

  appendAddPrinterButton(container)
}

function appendAddPrinterButton(container){
  var btn = document.createElement("BUTTON");
  var btntxt = document.createTextNode("+");

  btn.setAttribute("id", "add-network-printer");
  btn.appendChild(btntxt);
  container.appendChild(btn);
  $("#add-network-printer").click(function (e) { 
    console.log("add network printer button touched");
  });

  // Get the modal
  var modal = document.getElementById('myModal');
  var span = document.getElementsByClassName("close")[0];

  // When the user clicks on the button, open the modal 
  btn.onclick = function() {
    modal.style.display = "block";
  }
  // When the user clicks on <span> (x), close the modal
  span.onclick = function() {
    modal.style.display = "none";
  }
  // When the user clicks anywhere outside of the modal, close it
  window.onclick = function(event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
}



}
//   var hot = new Handsontable(container, {
//     data: data,
//     rowHeaders: true,
//     colHeaders: true,
//     filters: true,
//     dropdownMenu: true
//   });
  