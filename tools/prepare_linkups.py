import csv
from pathlib import Path

def prepare_linkups() -> None:
    """
    Compare the student (club survey) data and the master student data.
    Create a linkups file with the master student data and any names identified
    as being the same as those given in the survey, as well as a consume file
    with any students whose names were not found in the master student data,
    so they can be added by hand.
    """

    path_students_survey = Path('src/input/students_surveys.csv')
    path_students_master = Path('src/input/students_master.csv')
    path_linkups_stem = 'src/input/students_linkups'
    path_consume_stem = 'src/input/students_consume'

    students_survey = {}
    students_master = {}

    # Parse the student survey file and extract name, grade, and datestamp
    with open(path_students_survey, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)        
        next(reader)

        for row in reader:
            ds, name, grade = row[0].strip(), row[1].strip(), int(row[2])

            key = name.lower()
            while '  ' in key:
                key = key.replace('  ', ' ')

            students_survey[key] = {'name': name, 'grade': grade, 'ds': ds}

    # Parse the master student file and and parse name, grade, and gender
    # Also prepare a column for the survey name
    with open(path_students_master, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            _, sid, _, last, first, middle, _, _, gender, grade = (c.strip() for c in row[:10])
            students_master[sid] = {'first': first, 'last': last, 'middle': middle, 'grade': int(grade), 'gender': gender, 'survey': ''}

    # If the name (as first last) was on the survey, mark the column as 1
    # and remove them from the survey map (holds only unaccounted for ones)
    for (sid, d) in students_master.items():
        key = f'{d["first"]} {d["last"]}'.lower()
        if key in students_survey:
            d['survey'] = f'{d["first"]} {d["last"]}'
            del students_survey[key]

    # Determine the path for the linkups file; avoid overwriting any
    # (because the risk of losing work done by hand)
    stem = path_linkups_stem
    version = 0
    while Path(f'{stem}-{version:0>3}.csv').exists():
        version += 1

    path = Path(f'{stem}.csv') if not version else Path(f'{stem}-{version:0>3}.csv')

    # Write linkups, adding three more optional columns to be done by hand:
    # Status in the school, any days unavailable (TWR), and any notes
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Last name', 'First name', 'Middle name', 'Grade', 'Gender', 'Survey name', 'Exclude', 'Days unavailable', 'Notes'])

        for (sid, d) in students_master.items():
            writer.writerow([sid, d['last'], d['first'], d['middle'], d['grade'], d['gender'], d['survey'], '', '', ''])

    # Determine the path for the consume file; avoid overwriting any
    # (because the risk of losing work done by hand)
    stem = path_consume_stem
    version = 0
    while Path(f'{stem}-{version:0>3}.csv').exists():
        version += 1
    
    path = Path(f'{stem}.csv') if not version else Path(f'{stem}-{version:0>3}.csv')

    # Write consume, boiling it down to a student's survey date, name and grade
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'name', 'grade'])

        for (_, d) in students_survey.items():
            writer.writerow([d['ds'], d['name'], d['grade']])

if __name__ == '__main__': 
    prepare_linkups()
