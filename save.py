from __future__ import annotations

from pathlib import Path
import pickle
import csv
import os

from club import Club
from report import Report

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from school import School

# A bunch of constants :)

PATH_CLUB_VOTES = Path('src/output/club_votes/')
PATH_WORLD_REPORT_PICKLE_STEM = 'src/output/reports/{} final-report-pickle'
PATH_WORLD_REPORT_CLUBS_STEM = 'src/output/reports/{} final-report-clubs.csv'
PATH_WORLD_REPORT_STUDENTS_STEM = 'src/output/reports/{} final-report-students.csv'
PATH_WORLD_REPORT_DAYS_STEM = 'src/output/reports/{} final-report-days.csv'
PATH_WORLD_REPORT_TEACHERS_STEM = 'src/output/reports/{} final-report-teachers.csv'
PATH_WORLD_REPORT_STATS_STEM = 'src/output/reports/{} final-report-stats.csv'

DAY_TO_INT = {
    'T': 0,
    'W': 1,
    'R': 2
}

INT_TO_DAY_LETTER = ['T', 'W', 'R']

def save_summary_votes_csv(school: School, subset: str, report: Report|None=None) -> None:
    """
    Save a CSV of the votes that all clubs in the given school received.

    The subset indicates which snapshot it is; currently we're using 'raw',
    'filtered', and 'distributed' to indicate when in the program it happens.
    This allows distinguishing between original votes and effective votes after
    preselections, eligibility filtering, and so on.

    The columns are clubs; # of times chosen in top 3; upper limit / instance;
    # of students who got in (0 if no report is supplied); how many instances
    could be run based on interest; and then further vote count breakdowns.

    TODO Could probably eliminate the report part. It's in the output anyway.
    """
    clubs = school.clubs

    path = PATH_CLUB_VOTES / subset / f'_all-clubs [votes, {subset}].csv'
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Club', 'choices 123', 'upper limit', 'in after distribution', 'could run', 'choices 12345', '1', '2', '3', '4', '5'])

        for key in sorted(clubs.keys(), key=lambda k: -clubs[k].votes['123']):
            club = clubs[key]
            could_run = f'{club.get_ideal_n_instances()}x{club.days_per_instance}'
            
            # This only affects the distributed version, which we don't use
            n_students = report.n_students(club) if report else 0
            
            first_half = [key, club.votes['123'], club.upper, n_students, could_run, club.votes['12345']]
            writer.writerow(first_half + list(club.votes[key] for key in range(1, 6)))

def save_all_club_votes_csvs(school: School, subset: str) -> None:
    """
    Save the CSVs for club votes for all the clubs in the given school.

    The subset indicates which snapshot it is (see above).
    """
    for club in school.clubs.values():
        save_club_votes_csv(school, club, subset)

def save_club_votes_csv(school: School, club: Club, subset: str) -> None:
    """
    Save a CSV of the votes that a specific club received.

    The subset indicates which snapshot it is (see above).

    The columns are a student, their grade, and which choice they used for this
    club. Also, there are three rows with totals for the first three choices,
    the first five choices, and the preselections.
    """
    t123 = 0
    t12345 = 0
    tpre = 0

    student_to_choice = {}
    for student in school.students.values():        

        # If the student's choice is the club we're looking for, tally it
        for (key, other) in student.choices.items():
            if club.code == other:
                student_to_choice[student.name] = key
                t12345 += 1
                t123 += (key < 4)
                break

        # Also if they were preselected for this one
        for other in student.pres:
            if club.code == other:
                student_to_choice[student.name] = 'Preselected'
                tpre += 1

    keys = sorted(student_to_choice, key=lambda s: ((student_to_choice[s] if isinstance(student_to_choice[s], int) else 0), -school.students[s].grade))

    path = PATH_CLUB_VOTES / subset / f'{club.code} [votes, {subset}].csv'
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', newline="") as f:
        writer = csv.writer(f)
        writer.writerow(['Student', 'Grade', 'Choice'])
        writer.writerow(['[Total 123]', '', t123])
        writer.writerow(['[Total 12345]', '', t12345])
        writer.writerow(['[Total Preselected]', '', tpre])

        for key in keys:
            writer.writerow([key, school.students[key].grade, student_to_choice[key]])

def _sort_student(name: str) -> str:
    """
    Return the given student name in a sortable format.
    Students are sorted by last name (i.e., last space-split chunk).
    """
    return name.lower().split()[-1]

def pickle_report(report: Report, key: str) -> None:
    """
    Save a pickle of the given report with the given key identifier.
    """
    path = Path(PATH_WORLD_REPORT_PICKLE_STEM.format(key))
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'wb') as f:
        pickle.dump(report, f)

def unpickle_report(key: str) -> Report|None:
    """
    Load and return the pickle of the report with the given key.
    """
    path = Path(PATH_WORLD_REPORT_PICKLE_STEM.format(key))
    if not path.exists():
        return None

    with open(path, 'rb') as f:
        return pickle.load(f)

def resave_report(key: str) -> None:
    """
    Open and resave a pickled report. (This refreshes output formats.)
    Will be broken if data structures have changed.
    """
    report = unpickle_report(key)
    save_world_report(report, key)

def save_world_report_students_csv(report: Report, report_key: str) -> None:
    """
    Save a CSV of the given report with the given key, oriented by student.
    Gives a view from each student, sorted by last name, to the clubs they got.
    Also has columns for their grade and gender for alignment purposes.
    """
    path = Path(PATH_WORLD_REPORT_STUDENTS_STEM.format(report_key))
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Student', 'Grade', 'Gender', 'T', 'W', 'R'])

        for name in sorted(report.students, key=_sort_student):
            data = report.students[name]

            row = [name, data['grade'], data['gender']]

            # Using range to ensure days are sorted
            for i in range(3):
                if data['days'].get(i):

                    club = data['days'][i]
                    nice_club = data['nice names'][i]
                    instance = data['instance keys'][i]

                    # If there's only one instance, don't append the instance key
                    col = f'{nice_club} {instance}' if len(report.clubs[club]) > 1 else nice_club

                else:
                    col = ''

                row.append(col)

            writer.writerow(row)

def save_world_report_teachers_csv(report: Report, report_key: str) -> None:
    """
    Save a CSV of the given report with the given key, oriented by teacher.
    Gives a view from each teacher, sorted by name, to the clubs they got.
    """
    path = Path(PATH_WORLD_REPORT_TEACHERS_STEM.format(report_key))
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Teacher', 'T', 'W', 'R'])

        for name in sorted(report.teachers):
            data = report.teachers[name]

            row = [name]

            # Using range to ensure days are sorted
            for i in range(3):
                if data['days'].get(i):

                    club = data['days'][i]
                    nice_club = data['nice names'][i]
                    instance = data['instance keys'][i]

                    # If there's only one instance, don't append the instance key
                    col = f'{nice_club} {instance}' if len(report.clubs[club]) > 1 else nice_club
                else:
                    col = ''

                row.append(col)

            writer.writerow(row)

def save_world_report_clubs_csv(report: Report, report_key: str) -> None:
    """
    Save a CSV of the given report with the given key, oriented by club.
    Gives a view from each club, sorted by name, to its instance keys,
    and from there to the teacher, days running, number of students,
    and finally the students in each instance.
    """
    path = Path(PATH_WORLD_REPORT_CLUBS_STEM.format(report_key))
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Club', 'Group', 'Teacher', 'Days', '# Students', 'Students'])

        for club_code in sorted(report.clubs, key=lambda c: c.lower()):
            instances = report.clubs[club_code]
            for instance_key in sorted(instances):
                data = instances[instance_key]
                days, teacher, students, nice_name = data['days'], data['teacher'], data['students'], data['nice name']

                s_days = '/'.join((INT_TO_DAY_LETTER[i] for i in days))
                students = sorted(students, key=_sort_student)

                # Do not print an instance key if there's only one
                if len(instances) == 1:
                    instance_key = ''

                writer.writerow([nice_name, instance_key, teacher, s_days, len(students), *students])

def save_world_report_days_csv(report: Report, report_key: str) -> None:
    """
    Save a CSV of the given report with the given key, oriented by day.
    The columns are sets of days, and each row has the clubs (more specifically
    the club instances) running on that set of days, in alphabetical order.
    """

    keys = ['T', 'W', 'R', 'T/W', 'T/R', 'W/R', 'T/W/R']
    days_to_clubs = {key: [] for key in keys}

    # Map day variation to club code + instance key
    for club_code in sorted(report.clubs, key=lambda c: c.lower()):
        instances = report.clubs[club_code]
        for instance_key in sorted(instances):
            data = instances[instance_key]
            days = data['days']
            days_key = '/'.join((INT_TO_DAY_LETTER[i] for i in sorted(days)))
            days_to_clubs[days_key].append(f'{data["nice name"]} {instance_key}')

    # Transpose so it's columnwise for readability
    rows = [keys]
    for _ in range(len(max(days_to_clubs.values(), key=len))):
        rows.append(['', '', '', '', '', '', ''])

    for (i_col, key) in enumerate(keys):
        for (i_row, club) in enumerate(days_to_clubs.get(key, [])):
            rows[i_row + 1][i_col] = club

    # Save rows
    path = Path(PATH_WORLD_REPORT_DAYS_STEM.format(report_key))
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)

def save_world_report_stats_csv(report: Report, report_key: str) -> None:
    """
    Save a CSV of the statistics in the given report with the given key.
    The columns are simple keys and values from the report's stats.
    Full names for the keys are used rather than shorthand.

    TODO Sorting is just based on Python dictionary sorting
    TODO Could be aligned better with Report.format_report
    """
    path = Path(PATH_WORLD_REPORT_STATS_STEM.format(report_key))
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(Path(PATH_WORLD_REPORT_STATS_STEM.format(report_key)), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Key', 'Value'])
        writer.writerow(['Score', report.score])

        for (key, val) in report.stats.items():
            val = f'{val:.1f}'.rstrip('0').rstrip('.')

            # Append % to the values that are percentages
            if key.endswith('%'):
                val = f'{val}%'
            
            writer.writerow([report.full_names[key], val])

def save_world_report(report: Report, report_key: str) -> None:
    """
    Pickle the given report with the given key and save all view CSVs.
    """
    pickle_report(report, report_key)
    save_world_report_clubs_csv(report, report_key)
    save_world_report_students_csv(report, report_key)
    save_world_report_teachers_csv(report, report_key)
    save_world_report_days_csv(report, report_key)
    save_world_report_stats_csv(report, report_key)
