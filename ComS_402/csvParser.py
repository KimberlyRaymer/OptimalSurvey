import csv

def clean_up(input_file):
    # Open the input CSV file for reading and then writing
    with open(input_file, 'r') as file:
        # Create a CSV reader and writer
        reader = csv.reader(file)
        rows = list(reader)  # Read all rows into a list

        # Modify the rows by skipping the first two and the last row
        rows.pop(len(rows)-1) #pop the last row (test student) 
        rows.pop(1) #pop the second row (points possible) 
        modified_rows = rows 

    # Open the input CSV file again, but this time for writing
    with open(input_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(modified_rows)

    print(f"Processed CSV file saved as {input_file}")

