

import csv
import random
import math
from app import app
import os
import pandas as pd
import datetime
import automate_email

emailer = automate_email
'''
Run the simulated annealing function withs ids, prefs file and 
course name to generate CSVs that contain group matchings 
along with stats to measure performance.
'''

'''
This Simulated Annealing algorithm outperforms the original algorithm by a significant margin in terms of Total Preference
Scores across all group matchings, it also runs much faster (in less than 10 seconds) compared
to the original algorithm (30-40 seconds), and could still be optimized further in terms of time complexity.
'''

def convert_to_unix_timestamp(date_str, time_str):
    return int(datetime.datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M').timestamp())

def get_file_for_course(course, type):
    if type == "ids":
        ids_file = os.path.join(app.config['ABSOLUTE_PATH'] + app.config['STORAGE_FOLDER'], course + app.config['POSTFIX_IDS'])
        if os.path.isfile(ids_file):
            return ids_file
    elif type == "prefs":
        prefs_file = os.path.join(app.config['ABSOLUTE_PATH'] + app.config['STORAGE_FOLDER'], course + app.config['POSTFIX_PREFS'])
        if os.path.isfile(prefs_file):
            return prefs_file
def run_algorithm_for_courses(file_path):
    df = pd.read_csv(file_path)
    current_timestamp = datetime.datetime.now().timestamp()
    for index, row in df.iterrows():
        course = row['Course']
        deadline = row['Deadline']   
        size = row['Group Size']      
        deadline_timestamp = convert_to_unix_timestamp(deadline.split()[0], deadline.split()[1])
        if deadline_timestamp <= current_timestamp:
            if get_file_for_course(course, "ids") != None and get_file_for_course(course, "prefs") != None:
                simulated_annealing(get_file_for_course(course, "ids"), get_file_for_course(course, "prefs"), size, course)
                emailer.send_email_to_instructor(course)

def get_group(assign, num):
    return [item[0] for item in assign if item[1] == num]

def get_prefs_dict(prefs_data):
    return {((row[0]), (row[1])): int(row[2]) for _, row in prefs_data.iterrows()}

def get_score(group, prefs):
    pref_score = 0
    for first in range(len(group)):
        for second in range(first+1, len(group)):
            if second != first:
              pref_score += prefs.get((group[first], group[second]), 0)
              pref_score += prefs.get((group[second], group[first]), 0)
    return pref_score

def cost(groups, prefs):
    return -sum([get_score(group, prefs) for group in groups])

def count_no_positive_teammates(groups, prefs):
    count = 0
    students_with_prefs = [item[0] for item in prefs]
    
    for group in groups:
        for student in group:
            pref_exists = False
            for teammate in group:
                if prefs.get((student, teammate), 0) > 0:
                    pref_exists = True
                    break
            if not pref_exists and student in students_with_prefs:
                count += 1
    return count

def simulated_annealing(ids_file, prefs_file, n, course_name, experiment_runs=25):
    ids = pd.read_csv(ids_file, header = None).iloc[:, 0].tolist()
    if ids[0] == 'SIS Login ID':
        ids.pop(0)
    prefs = get_prefs_dict(pd.read_csv(prefs_file, header = None))
    best_score = float('-inf')
    best_score_2 = float('-inf')
    best_count = float('inf')
    best_count_2 = float('inf')

    best_table_score = None
    best_table_count = None

    # count the number of groups in a dynamic way using this formula
    no_of_groups = int(len(ids) / n) + (len(ids) % n != 0)

    for _ in range(experiment_runs):
        curr = []
        for id in range(0, len(ids), n):
          group = ids[id:id+n]
          curr.append(group)
        current_cost = cost(curr, prefs)
        # set an init temperature
        initial_temp = 1000
        # set a cooling rate based on which it would accept "bad" solutions
        cooling_rate = 0.995 + random.uniform(-0.005, 0.005)
        # cap the number of iterations
        iterations = 10000
        temperature = initial_temp

        for _ in range(iterations):
            sol = [group.copy() for group in curr]
            first_group, second_group = random.sample(sol, 2)
            member1, member2 = random.choice(first_group), random.choice(second_group)
            # randomly swap group members between 2 diff groups. 
            if member1 != member2:
              first_group.remove(member1)
              second_group.remove(member2)
              first_group.append(member2)
              second_group.append(member1)
            new_cost = cost(sol, prefs)
            # accept suboptimal solutions with some probabbility e^(cost_diff) / t
            if new_cost < current_cost or random.random() < math.exp((current_cost - new_cost) / temperature):
                curr, current_cost = sol, new_cost
            # decrease temperature according to cooling rate after each iteration    
            temperature *= cooling_rate
        results = []
        for group_number, group in enumerate(curr, 1):
             for net_id in group:
                results.append((net_id, group_number))
        score = -current_cost

        sa_groups = []
        for group_num in range(1, no_of_groups + 1):
            group = get_group(results, group_num)
            sa_groups.append(group)

        count_sa = count_no_positive_teammates(sa_groups, prefs)
        # Save the group assingments with max preference score so far.
        if score > best_score or (score == best_score and count_sa < best_count_2):
            best_score = score
            best_count_2 = count_sa
            best_table_score = results
        # Save the group assignments with least number of students who didn't get their prefs so far.
        if count_sa < best_count or (count_sa == best_count and score > best_score_2):
            best_score_2 = score
            best_count = count_sa
            best_table_count = results

    # Save best results and stats measuring performance to CSVs.
    with open(os.path.join(app.config['ABSOLUTE_PATH'] + app.config['STORAGE_FOLDER'], course_name + '_best_by_score.csv'), 'w', newline='') as groups_by_score:
        write = csv.writer(groups_by_score)
        for row in best_table_score:
            write.writerow(row)
    with open(os.path.join(app.config['ABSOLUTE_PATH'] + app.config['STORAGE_FOLDER'], course_name + '_best_by_score_stats.csv'), 'w', newline='') as score_stats:
        write = csv.writer(score_stats)
        write.writerow(["Total Preference Score", "No of Students without preferred teammates"])
        write.writerow([best_score, best_count_2])
    print(f"Best Solution (optimized on pref scores): {best_score}")
    print(f"Number of students without a preferred teammate: {best_count_2}")
    for row in best_table_score:
        first, second = row
        print(str(first) + ", " + str(second))
    with open(os.path.join(app.config['ABSOLUTE_PATH'] + app.config['STORAGE_FOLDER'], course_name + '_best_by_prefs.csv'), 'w', newline='') as groups_by_prefs:
        write = csv.writer(groups_by_prefs)
        for row in best_table_count:
            write.writerow(row)
    with open(os.path.join(app.config['ABSOLUTE_PATH'] + app.config['STORAGE_FOLDER'], course_name + '_best_by_prefs_stats.csv'), 'w', newline='') as prefs_stats:
        write = csv.writer(prefs_stats)
        write.writerow(["Total Preference Score", "No of Students without preferred teammates"])
        write.writerow([best_score_2, best_count])
    print(f"Best Solution (optimized on no. of students who didn't get their preferences): {best_score}")
    print(f"Number of students without a preferred teammate: {best_count}")
    for row in best_table_count:
        first, second = row
        print(str(first) + ", " + str(second))



if __name__ == "__main__":
    #if you get an error here while testing locally, check ABSOLUTE_PATH in app.py
    all_course_data_path = os.path.join(app.config['ABSOLUTE_PATH'] + app.config['STORAGE_FOLDER'], app.config['COURSE_DATA_FILE'])
    run_algorithm_for_courses(all_course_data_path)






