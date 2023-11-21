

import json
import smtplib
from flask import Flask, request, redirect, jsonify, session
from routes import routes
from routes import swaggerui_blueprint
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import time
import pandas as pd
import os
import csv
import traceback
import random
import string
import csvParser
import automate_email
import secrets

parser = csvParser
emailer = automate_email


app = Flask(__name__, template_folder="frontend")
app.register_blueprint(routes)
app.register_blueprint(swaggerui_blueprint)
app.config['STORAGE_FOLDER'] = 'optimalgroups_csv_storage' 
app.config['NET_ID_IDENTIFIER'] = 'SIS Login ID'
app.config['COURSE_DATA_FILE'] = 'course_data.csv'
app.config['POSTFIX_IDS'] = '_Classlist.csv'
app.config['POSTFIX_PREFS'] = '_prefs.csv'

# needed to prevent tampering of session data
app.config['SECRET_KEY'] = secrets.token_hex(16)

# needed to add this to execute the algorithm using the cron job 
# This may cause issues with local Testing
#app.config['ABSOLUTE_PATH'] = os.path.join(os.path.expanduser("~"), "loop2/optimal-groups/ComS_402/")
app.config['ABSOLUTE_PATH'] = r'D:\\Homework\\COM S 402\\optimal-groups-copy\\optimal-groups\\ComS_402\\'
def modify_file(file_path, choice, value_list):
    with open(file_path, choice, newline='') as file:
        writer = csv.writer(file)
        writer.writerow(value_list)
def course_exists(file_path, course_name):
    df = pd.read_csv(file_path)
    if course_name in df['Course'].values:
        return True
    return False

# Generates unique verification codes for the students in the class
def generate_codes(listLength, codeLength):
    codes = []
    random_string = ""
    characters = string.ascii_letters + string.digits  # Letters and numbers
    for x in range(listLength):
        random_string = ''.join(random.choice(characters) for _ in range(codeLength))
        while random_string in codes or random_string == "":
            random_string = ''.join(random.choice(characters) for _ in range(codeLength))
        codes.append(random_string)
    return codes

# returns the email that received the authentication code
@app.route('/get-email', methods=['GET']) 
def get_email():
    with open('config.json', 'r') as json_file:
        config_data = json.load(json_file)
    email = config_data['instructor']
    return jsonify(email)

#Checks if the current stored authentication code is valid, if not send a new one
#returns "new_code" signalling we sent a brand new code
#returns "current_code" signalling to use the current code send less than 24 hours ago
@app.route('/send-code', methods=['GET']) 
def send_code():
    with open('config.json', 'r') as json_file:
        config_data = json.load(json_file)

    due_date_str = config_data['Due_Date']
    expire_date = datetime.strptime(due_date_str, "%Y-%m-%d %H:%M:%S.%f")

    if datetime.now() >= expire_date:
        new_code = generate_codes(1, 7)[0]  # Get the first code from the list
        current_time = datetime.now()
        expire_date = current_time + timedelta(hours=24)

        # Update the "current_code" key as a string
        config_data["current_code"] = new_code

        config_data["Due_Date"] = expire_date.strftime("%Y-%m-%d %H:%M:%S.%f")

        # Write the updated data back to the JSON file
        with open('config.json', 'w') as json_file:
            json.dump(config_data, json_file, indent=4)
        emailer.send_verication_code()
        print('sent new code: ' + str(new_code))
        return jsonify("new_code")
    else:
        print('using old code: '+ str(config_data["current_code"]))
        return jsonify("current_code")

#This is a POST method used to check the code given by instructor to the code currently stored
#returns    expired -> new code was generated and sent to instructor
#returns    success -> code provided matched current code and proceed as normal
#return     fail    -> code provided didnt match current code, ask again for correct code
@app.route('/check-code', methods=['POST']) 
def check_code():    
    data = request.get_json()
    check_code = data.get('codeInput')
    print("check_code", check_code)
    with open('config.json', 'r') as json_file:
        config_data = json.load(json_file)
    due_date_str = config_data['Due_Date']
    expire_date = datetime.strptime(due_date_str, "%Y-%m-%d %H:%M:%S.%f")
    current_code = config_data['current_code']
    
    #This checks if the Due Date passes while the page is currently open asking for code
    #Copied from GET method above
    if datetime.now() >= expire_date:
        new_code = generate_codes(1, 7)[0]  # Get the first code from the list
        current_time = datetime.now()
        expire_date = current_time + timedelta(hours=24)
        config_data["current_code"] = new_code  # Store as a single string

        # Update the "current_code" key as a string
        config_data["current_code"] = new_code

        config_data["Due_Date"] = expire_date.strftime("%Y-%m-%d %H:%M:%S.%f")

        # Write the updated data back to the JSON file
        with open('config.json', 'w') as json_file:
            json.dump(config_data, json_file, indent=4)
        emailer.send_verication_code()
        print('sent new code: ' + str(new_code))
        return "expired"
    elif(check_code == current_code):
        print("check_code success", check_code )
        session["verified"] = True
        return "success", 200
    
    else:
        print("check_code fail", check_code )
        return "fail", 400
    

@app.route('/submit-form', methods=['POST'])
def upload_file():

    instructor_csv = request.files['file']
    group_size = request.form.get('groupSize') 
    deadlineDate = request.form.get('deadlineDate') 
    deadlineTime = request.form.get('deadlineTime')
    deadline = deadlineDate + " " + deadlineTime
    course = request.form.get('course') or 'default_course'
    course = course.replace(" ", "_")
    file_path = os.path.join(app.config['STORAGE_FOLDER'], secure_filename(
        course + '_Classlist.csv'))
    all_course_data_path = os.path.join(app.config['STORAGE_FOLDER'], app.config['COURSE_DATA_FILE'])
    temp_csv = pd.read_csv(instructor_csv)
    
    try:
        netid_and_names = temp_csv[[app.config['NET_ID_IDENTIFIER'], 'Student']]
    except KeyError:
        return "Error: Please upload a CSV with " +  "Specified Net Id column named: " + app.config['NET_ID_IDENTIFIER'], 400 
    
    if not course_exists(all_course_data_path, course):
        modify_file(all_course_data_path, 'a', [course, deadline, group_size])
    else:
        return redirect('/frontend/errorDuplicateCourse.html')

    add_codes_df = pd.DataFrame()
    add_codes_df['SIS Login ID'] = temp_csv[app.config['NET_ID_IDENTIFIER']]
    add_codes_df['Student'] = temp_csv['Student']
    add_codes_df['Verification Code'] = generate_codes(len(temp_csv[app.config['NET_ID_IDENTIFIER']]), 8)
    add_codes_df.to_csv(file_path, index=False)
    
    parser.clean_up(file_path)
    
    course_info_data = [["Course", "Deadline", "Group Size"],
                    [course, deadline, group_size]]

    if not os.path.isfile(all_course_data_path):
        modify_file(all_course_data_path, 'w', course_info_data[0])
  
    emailer.send_email_to_students(file_path, course, deadline)

    session.clear()
    return redirect('/frontend/success.html')

@app.route('/get-netids', methods=['GET'])
def get_netids():
    # Grab parameters from the URL
    studentCode = request.args.get('code')
    courseName = request.args.get('course') 
    classlist_file_path = app.config['STORAGE_FOLDER'] + '/' + courseName + '_Classlist.csv'
    pref_file_path = os.path.join(app.config['STORAGE_FOLDER'], secure_filename(courseName + '_prefs.csv'))
    all_course_data_file_path = os.path.join(app.config['STORAGE_FOLDER'], app.config['COURSE_DATA_FILE'])

    # Making sure the url link includes both course name and verification code
    if studentCode == "null" or courseName == "null":
        return jsonify("invalid link"), 400
    
    # if the course instructor did not upload a classlist csv
    if not os.path.isfile(classlist_file_path):
        return jsonify("This course does not use the Optimal Groups survey"), 400

    classlist_df = pd.read_csv(classlist_file_path)
    all_course_data_df = pd.read_csv(all_course_data_file_path)
    # Check if the student is in the uploaded classlist
    try:
        studentName = classlist_df.loc[classlist_df['Verification Code'] == studentCode,'Student'].iloc[0]
    except:
        return jsonify("Student is not in this class"), 400
    
    if os.path.isfile(pref_file_path) :
        prefs_df = pd.read_csv(pref_file_path, header = None)
        recipient_netid = classlist_df.loc[classlist_df['Verification Code'] == studentCode, 'SIS Login ID'].iloc[0]

        # Ensures that a student won't retake the survey they already completed
        if recipient_netid in prefs_df[0].values:
            return jsonify("Survey has already been taken"), 400
    

    desiredRow = all_course_data_df[all_course_data_df["Course"] == courseName]
    currentDate = datetime.now()
    surveyDeadline = datetime.strptime(desiredRow.iloc[0]["Deadline"], '%Y-%m-%d %H:%M')
    
    if currentDate > surveyDeadline:
        return jsonify("Deadline has passed"), 400    
    
    classlist_df = classlist_df.rename(columns={'SIS Login ID': 'netid', 'Student' : 'names'})
    
    # Removes the row containing the recipient student's name
    removedName = classlist_df['names'] == studentName
    classlist_df = classlist_df[~removedName]
    
    dataDict = {"students": classlist_df.to_dict(orient='records')}
    jsonData = jsonify(dataDict)
    return jsonData

@app.route('/submit-survey', methods=['POST'])
def submit():
        data = request.get_json()
        # recipient's survey results
        survey_results = data.get('teammateList')
        course = data.get('course')
        recipient_code = data.get('code')
    
        pref_file_path = os.path.join(app.config['STORAGE_FOLDER'], secure_filename(course + '_prefs.csv'))
        netid_file_path = os.path.join(app.config['STORAGE_FOLDER'], secure_filename(course + '_Classlist.csv'))
        all_course_data_file_path = os.path.join(app.config['STORAGE_FOLDER'], app.config['COURSE_DATA_FILE'])

        classlist_df = pd.read_csv(netid_file_path)
        all_course_data_df = pd.read_csv(all_course_data_file_path)

        recipient_netid = classlist_df.loc[classlist_df['Verification Code'] == recipient_code, 'SIS Login ID'].iloc[0]
        
        desiredRow = all_course_data_df[all_course_data_df["Course"] == course]
        currentDate = datetime.now()
        surveyDeadline = datetime.strptime(desiredRow.iloc[0]["Deadline"], '%Y-%m-%d %H:%M')
        
        # Handles case where student has the survey opened before deadline but submits after deadline
        if currentDate > surveyDeadline:
            return "Deadline has passed", 400
        
        # creates/updates the course prefs csv
        if os.path.exists(pref_file_path):
            prefs_df = pd.read_csv(pref_file_path, header=None)
            recipient_netid = classlist_df.loc[classlist_df['Verification Code'] == recipient_code, 'SIS Login ID'].iloc[0]

            # Ensures that a student won't retake the survey they already completed
            if recipient_netid in prefs_df[0].values:
                return "Survey has already been taken", 400
        else:
            prefs_df = pd.DataFrame()

        teammates_data = []
        ranking_data =[]

        for teammate in survey_results:
            pref_rank = teammate[-1]
            teammates_data.append(teammate[:-1])

            if pref_rank == '1':
                pref_rank = '4'
            elif pref_rank == '2':
                pref_rank = '3'
            elif pref_rank == '3':
                pref_rank = '2'
            elif pref_rank == '4':
                pref_rank = '1'
            elif pref_rank == '5':
                pref_rank = '-10'
            elif pref_rank == '6':
                pref_rank = '-10'
        
            ranking_data.append(pref_rank)
        # Example prefs csv has no column headers so this one won't either
        # 0 -> Recipient, 1 -> Teammate Chosen, 3 -> Preference Points
        new_survey_data = pd.DataFrame({
            0: [recipient_netid] * len(teammates_data),
            1: teammates_data,
            2: ranking_data
        })
        new_survey_data = new_survey_data.sort_values(2, ascending=False)
        prefs_df = pd.concat([prefs_df, new_survey_data], ignore_index=True)
        prefs_df.to_csv(pref_file_path,index=False, header=False)
        
        return redirect('/frontend/thanks.html')

if __name__ == '__main__':
    app.run(debug=True)

