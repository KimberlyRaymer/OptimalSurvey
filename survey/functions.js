//Object for createPrefers
const tableInfo = {
    "num_radio": 4,
    "table" : "nonPreferTable",
    "tableCells" : 5
};

// function postForm(event) {
    //Prevent form from submitting data right away
    // event.preventDefault();
    // form.action = "http://coms-402-001.class.las.iastate.edu:5000/";
    // setTimeout(() => {
        // fetch('http://coms-402-001.class.las.iastate.edu:5000/get_json_data')

        // .then(response => response.json())
        // .then(data => {
        //     console.log(data);
        // })
        // .catch(error => {
        //     console.error(error);
        // });

        // window.location.href = "preferences.html";

    // }, 2000);

// }

//For the next buttons
//Switches to the correct html page
function switchWindow(event) {
    if (document.URL.includes("survey.html")) {
        event.preventDefault();
        window.location.href = "preferences.html";
    }
    else if (document.URL.includes("preferences.html")){
        window.location.href = "non_prefer.html";
    }
    else {
        window.location.href = "thanks.html";
    }
}

//This function is to hold array of preferences from user
function preferences(num_radio) {
    for (var i = 0; i < numStudents; i++) {
        for (var j = 0; j < num_radio; j++) {
            // if (document.getElementById([students[j].value])) {}
            console.log(document.getElementById(students[i].value + i]));
        }
    }
}

var netids = ["johndoe", "janedoe", "jackdoe", "jerrydoe"];  //for testing only
var students = ["john doe", "jane doe", "jack doe", "jerry doe"];  //for testing only

// helper method to createPrefers
// creates the radio buttons
var elems = [];
function createBttns(id, radios) {
    for (var i = 0; i < radios; i++) {
        let radioBttn = document.createElement("input");
        radioBttn.type = "radio";
        radioBttn.value = i + 1;
        radioBttn.name = id;
        radioBttn.id = id + i;
        elems.push(radioBttn);
    }
}

//helper method to create tds
// function createTD (incrementTD, totalCells, tableCells, tr) {
//     for (var j = incrementTD; j < totalCells; j++) {
//         td[j] = document.createElement('td');
//         console.log(td[j]);
//         if (j % tableCells == 0) {
//             var text = document.createTextNode(students[i]);
//             td[j].appendChild(text);
//         }
//         else {
//             td[j].className = "radioBox";
//             td[j].appendChild(elems[numElems]);
//             numElems++;
//         }
//         tr[i].appendChild(td[j]);
//     }
// }

//dynamically generate preference list table
var numStudents = students.length;
var td = [];
var tr = [];
function createPrefers(table, numRadios, tableCells) {
    var incrementTD = numElems = 0;
    var totalCells = tableCells;

    for (var i = 0; i < numStudents; i++){
        tr[i] = document.createElement('tr');

        createBttns(netids[i], numRadios);

        for (var j = incrementTD; j < totalCells; j++) {
            td[j] = document.createElement('td');
            console.log(td[j]);
            if (j % tableCells == 0) {
                var text = document.createTextNode(students[i]);
                td[j].appendChild(text);
            }
            else {
                td[j].className = "radioBox";
                td[j].appendChild(elems[numElems]);
                numElems++;
            }
            tr[i].appendChild(td[j]);
        }

        table.appendChild(tr[i]);

        incrementTD += tableCells;
        totalCells += tableCells;
    }
}

// function maxChecked () {
//     if (document.querySelectorAll('input[type="checkbox"]:checked').length == 4) {

//     }

// }