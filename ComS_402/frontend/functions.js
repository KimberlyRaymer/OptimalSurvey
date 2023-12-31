//------------------------------------- VERIFICATION PAGE FUNCTIONS -------------------------------------

//get request for verification code sent to the instructor
function getVerificationCode() {
    return fetch('/send-code')
        .then(jsonData => jsonData.json())
        .then(data => {
            return data;
        })
        .catch((error) => {
            console.log("Verification Code Status: " + error.status);
        });
}

//get instuctor's email to display in verification page
function getInstructorEmail() {
    return fetch('/get-email')
        .then(jsonData => jsonData.json())
        .then(data => {
            return data;
        })
        .catch((error) => {
            console.log("Email Status: " + error.status);
        });
}

//post instructor input verification code
function postVerificationCode(code) {
    verificationForm = document.getElementById("verificationForm")
    var codeInput = {"codeInput": code}
    fetch('/check-code', {
            method : 'POST',
            headers : {
                'Content-Type' : 'application/json'
            },
            body : JSON.stringify(codeInput)
        })
    .then(response => {
        return response.text();
    })
    .then(status => {
        (status === 'success') ? window.location.href = "upload.html" : alert("Invalid code, please try again");
    })
    .catch((error) => {
        console.log("Post Status: " + error);
        alert("Error"); 
    });   
    verificationForm.reset(); // reset form inputs
    return false // to prevent form submission if redirect to upload.html did not happen
}

//input instructor email into specific container
function displayEmail(email) {
    document.getElementById("emailContainer").innerHTML = (email != null)? email : "Email could not be fetched, please check your school email";
}

//generate individual inputs for code
//can adjust number of inputs based off of verification code length
function createCodeInputs(inputLength) {
    const input = document.getElementById('verificationInputs');
    for (let i = 0; i < inputLength; i++) {
      var elem = document.createElement('input');
      elem.className = "codeInput";
      elem.id = 'codeInput' + i;
      elem.maxLength = 1;
      input.appendChild(elem);
    }
}

//allows users to go forward and back with arrows keys
function moveBetweenInputs() {
    const inputs = document.querySelectorAll('#verificationInputs > *[id]');
    //select all ids under verificationInputs div container
    var lastIndex = inputs.length - 1;
    for (let i = 0; i < inputs.length; i++) {
        //check which key user clicks on
        inputs[i].addEventListener('keydown', function(e) {
            if (e.key === "Backspace") {
                //nothing is in the input and backspace clicked
                if (inputs[i].value == '') {
                    //then go to the previous input - make sure to not go less than index 0 (e.g. -1...)
                    if (i != 0) {
                    //focus on the previous input
                    inputs[i - 1].focus();
                    }
                } else {
                    //something was in input, clear
                    inputs[i].value = '';
                }
            //don't go beyond 0 index
            } else if (e.key === "ArrowLeft" && i !== 0) {
                inputs[i - 1].focus();
            //don't go beyond last input index
            } else if (e.key === "ArrowRight" && i !== lastIndex) {
                inputs[i + 1].focus();
            } 
        });
        inputs[i].addEventListener('input', function() {
            if (i === lastIndex && inputs[i].value !== '') {
                return true;
            } else if (inputs[i].value !== '') {
                inputs[i + 1].focus();
            }
      });
    }
}

//get input values
function getCodeInputVals() {
    const inputs = document.querySelectorAll('#verificationInputs > *[id]');
    let code = '';
    for (let i = 0; i < inputs.length; i++) {
        code += inputs[i].value;
    }
    return code;
}

//------------------------------------- VERIFICATION PAGE ENDED -------------------------------------

//gets student names and ids from a get request
//stored in global variable names and net_ids
const names = [];
const net_ids = [];
var numStudents = 0;
function getStudents(data) {
    const list = data;
    console.log("Parsed JSON data:", list);

    for (var i = 0; i < list.students.length; i++) {
        console.log("Processing student:", list.students[i].names);
        names.push(list.students[i].names);
        net_ids.push(list.students[i].netid);

    }
    // ensure that net_ids is populated before createPrefers is called
    numStudents = net_ids.length
}

// helper method to createPrefers
// creates the radio buttons
var elems = [];
function createBttns(id, radios) {
    for (var i = 0; i < radios; i++) {
        let radioBttn = document.createElement("input");
        radioBttn.type = "radio";
        radioBttn.className = "radioButton";
        radioBttn.value = id + (i + 1);
        radioBttn.name = id;
        radioBttn.id = id + (i + 1);
        radioBttn.dataset.col = (i + 1);
        elems.push(radioBttn);
    }
}

//dynamically generate preference list table
//create one textNode for student name
//create equivalent amt of radio buttons as numRadios
var td = [];
var tr = [];
function createPrefers(table, numRadios, tableCells) {

    var numElems = 0;

    for (var i = 0; i < numStudents; i++){

        tr[i] = document.createElement('tr');
        createBttns(net_ids[i], numRadios);

        for (var j = 0; j < tableCells; j++) {

            td[j] = document.createElement('td');

            //checks if it is the first cell for student name
            if (j % tableCells == 0) {
                var text = document.createTextNode(names[i]);
                td[j].className = "studentCell";
                td[j].appendChild(text);
            }
            //else create radio buttons
            else {
                //if non-preferences
                if (j >= numRadios - 1) {
                    td[j].className = "nonRadioBox";
                }
                else {
                    td[j].className = "radioBox";
                }
                // var label = document.createElement("label");
                // label.appendChild(elems[numElems]);
                td[j].appendChild(elems[numElems]);
                numElems++;
            }
            tr[i].appendChild(td[j]);
        }

        table.appendChild(tr[i]);
    }
}

//dynamically creates table
function makeTable() {
    var table = document.getElementById("preferenceTable");
    //adjust the number of radio buttons per row
    var num_radio = 6;
    //adjust the number of total table cells per row (student td td td...)
    var tableCells = 7;
    createPrefers(table, num_radio, tableCells);
}

//allows selection and deselection of radio buttons
function radioSelection() {
    //button is checked when clicked, and marked as checked
    $('input[type=radio].radioButton').on('mousedown', function(e){
        var checked = $(this).prop('checked');
        this.turnOff = checked;
        $(this).prop('checked', !checked);
    });

    //button is clicked again to deselect/turn off
    //clicked is to ensure that all other buttons surrouding the clicked button are cleared
    $('input[type=radio].radioButton').on('click', function(e){
        var clicked = $(e.target);
        $(".radioButton[data-col=" + clicked.data("col") + "]").prop("checked", false);
        $(this).prop('checked', !this.turnOff);
        this['turning-off'] = !this.turnOff;
    });
    
}

//another option that allows radio buttons to be selected and unselected
function allowSelection() {
    //for selection and deselection of radio buttons
    var allRadios = document.querySelectorAll('input[type=radio]');
    var selectedRadio;
    var i = 0;
    for (i = 0; i < allRadios.length; i++) {
        allRadios[i].onclick = function(e) {
            var clicked = $(e.target);
            if (selectedRadio == this) {
                this.checked = false;
                selectedRadio = null;
            } else {
                $(".radioButton[data-col=" + clicked.data("col") + "]").prop("checked", false);
                this.checked = true;
                selectedRadio = this;
            }
        };
    }
}


//This function is to hold an array of prefered and non-prefered teammates from user
function preferences() {

    const teammates = [];
    let radioBttn;
    var num_radio = 6;

    for (var i = 0; i < net_ids.length; i++) {
        for (var j = 0; j < num_radio; j++) {
            radioBttn = document.getElementById(net_ids[i] + (j + 1));
            if (radioBttn.checked) {
                teammates.push(radioBttn.value);
              }
        }
    }

    localStorage.setItem("teammates", JSON.stringify(teammates));
    postTeammateArray()
}


//to obtain user's preferences and non-preferences and post to the server
function postTeammateArray() {
    const course = getCourseFromURL();
    const code = getCodeFromURL();
    const teammateList = JSON.parse(localStorage.getItem("teammates"));
    const postData = {"teammateList" : teammateList, "course" : course, "code" : code}

    fetch('/submit-survey', {
        method : 'POST',
        headers : {
            'Content-Type' : 'application/json'
        },
        body : JSON.stringify(postData)
    })
    .then(response => {
        if(response.redirected) {
            window.location.href = response.url
        }
        else {
            return response.text();
        }
    })
    .then(data => {
        if(data === "Survey has already been taken") {
            window.location.href = "/frontend/error403.html"
        }
        if(data === "Deadline has passed") {
            window.location.href = "/frontend/errorDeadline.html"
        }
    })
}


//-----------------Extra methods that are used for all three pages-----------------

//For the next buttons
//Switches to the correct html page
// function switchWindow(event) {
//     if (document.URL.includes("survey.html")) {
//         event.preventDefault();
//         window.location.href = "preferences.html";
//     }
//     else if (document.URL.includes("preferences.html")){
//         window.location.href = "non_prefer.html";
//     }
//     else {
//         window.location.href = "thanks.html";
//     }
// }