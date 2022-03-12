from pathlib import Path
import csv

def sort_study_halls() -> None:
    """
    Sort the output study halls into grades and save a CSV of the result.
    """
    path_students = Path('src/output/reports/A final-report-students.csv')
    path_clubs = Path('src/output/reports/A final-report-clubs.csv')
    path_sorted = Path('src/output/reports/A final-report-study-halls.csv')

    # Read students into a map of name to grade
    name_to_grade = {}
    with open(path_students, 'r') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            name, grade, *_ = row
            name_to_grade[name] = int(grade)

    # Read clubs into a map of day to students in Study Hall on that day
    day_to_students = {}
    with open(path_clubs, 'r') as f:

        reader = csv.reader(f)
        next(reader)

        for row in reader:
            club, _, _, day, n, *students = row

            if club == 'Study Hall':
                day_to_students[day] = day_to_students.get(day, []) + students
    
    # For each day, divide students into buckets by grade
    day_to_grade_buckets = {}
    for (day, students) in day_to_students.items():
        day_to_grade_buckets[day] = {9: [], 10: [], 11: [], 12: []}
        for student in students:
            grade = name_to_grade[student]
            if grade == 13:
                grade = 12
            day_to_grade_buckets[day][grade].append(student)

    # Full names for days for your reading pleasure
    day_to_full = {'T': 'Tues', 'W': 'Wed', 'R': 'Thurs'}

    # Output a CSV where each day is grouped into grades        
    with open(path_sorted, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Day', 'Grade', 'Students'])

        for (day, grade_to_students) in day_to_grade_buckets.items():
            for (grade, students) in grade_to_students.items():
                writer.writerow([])
                writer.writerow([day_to_full[day], grade, f'{len(students)} students'])
                writer.writerow([])
                for student in students:
                    writer.writerow([day_to_full[day], grade, student])

            writer.writerow([])
                
if __name__ == '__main__': 
    sort_study_halls()
