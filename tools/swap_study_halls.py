from pathlib import Path
import csv

def swap_study_halls() -> None:
    """
    Take the study hall members as sorted by hand and swap students into them.
    """
    swaps_stem = Path('src/reference/sorted_study_halls.csv')

    students_stem = Path('src/output/reports/A final-report-students.csv')
    students_fix_stem = Path('src/output/reports/A final-report-students-swapped.csv')
    clubs_stem = Path('src/output/reports/A final-report-clubs.csv')
    clubs_fix_stem = Path('src/output/reports/A final-report-clubs-swapped.csv')

    student_to_halls = {}
    hall_to_students = {}

    # Read the swaps into a dict of students to the hall they should be in,
    # and a dict of halls to the students who are in them
    with open(swaps_stem, 'r') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            if not any(row):
                continue

            student, *halls = row
            
            if student not in student_to_halls:
                student_to_halls[student] = ['', '', '']
            
            for i in range(3):
                hall = halls[i]
                if hall:
                    student_to_halls[student][i] = hall

                hall_to_students[hall] = hall_to_students.get(hall, []) + [student]

    # Swap the students into the said study halls in the students file
    with open(students_stem, 'r') as old:
            reader = csv.reader(old)
            next(reader)

            with open(students_fix_stem, 'w', newline='') as new:
                writer = csv.writer(new)
                writer.writerow(['Student', 'Grade', 'Gender', 'T', 'W', 'R'])

                for row in reader:
                    if not any(row):
                        continue

                    student, grade, gender, *clubs = row
                    for i in range(3):
                        if 'Study Hall' in clubs[i]:
                            clubs[i] = f'Study Hall {student_to_halls[student][i]}'

                        # Fudge split clubs into instance keys
                        # TODO Ridiculous stopgap...
                        if 'Cosmetology 1' in clubs[i]:
                            clubs[i] = 'Cosmetology A'
                        if 'Cosmetology 2' in clubs[i]:
                            clubs[i] = 'Cosmetology B'
                        if 'Self-Defence 1' in clubs[i]:
                            clubs[i] = 'Self-Defence B'
                        if 'Self-Defence 2' in clubs[i]:
                            clubs[i] = 'Self-Defence B'

                    writer.writerow([student, grade, gender, *clubs])

    # Swap the students into the said study halls in the clubs file
    with open(clubs_stem, 'r') as old:
            reader = csv.reader(old)
            next(reader)

            with open(clubs_fix_stem, 'w', newline='') as new:
                writer = csv.writer(new)
                writer.writerow(['Club', 'Group', 'Teacher', 'Days', '# Students', 'Students'])

                for row in reader:
                    if not any(row):
                        continue

                    club, instance, teacher, days, n, *students = row

                    if 'Study Hall' in club:
                        students = hall_to_students[instance]
                        n = len(students)

                    writer.writerow([club, instance, teacher, days, n, *students])

if __name__ == '__main__': 
    swap_study_halls()
