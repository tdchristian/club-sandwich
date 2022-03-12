from __future__ import annotations

from pathlib import Path
import csv

from input_file import InputFile, InputFileColumn

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from school import School

# Lots of path constants :)

PATH_STUDENTS = Path('src/input/students_surveys.csv')
PATH_LINKUPS = Path('src/input/students_linkups.csv')
PATH_CLUBS = Path('src/input/clubs.csv')
PATH_PRESELECTS = Path('src/input/preselects.csv')
PATH_WHITELISTS = Path('src/input/whitelists.csv')
PATH_BLACKLISTS = Path('src/input/blacklists.csv')
PATH_CLUB_REPORTS = Path('src/output/club_reports/')
PATH_MERGES = Path('src/input/merges.csv')
PATH_SPLITS = Path('src/input/splits.csv')
PATH_NICE_NAMES = Path('src/input/renames.csv')
PATH_EXCLUSIONS = Path('src/input/exclusions.csv')
PATH_INPUT_SPECS = Path('src/input/_input_specifications.csv')

DAY_TO_INT = {
    'T': 0,
    'W': 1,
    'R': 2
}

def parse_merges(school: School) -> None:
    """
    Ingest the merges file and register each one with the school.

    A merge causes two different club names to be treated as one
    from this point forward.
    """
    if not PATH_MERGES.exists():
        return

    with open(PATH_MERGES, 'r') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            if not any(row):
                continue

            # absorb is absorbed into main, not vice versa            
            main, absorb = (school.normalize_club_code(c.strip()) for c in row)
            school.add_merge(main, absorb)

def parse_splits(school: School) -> None:
    """
    Ingest the splits file and register each one with the school.

    A split causes a club name to branch into two or more with supplied names
    from this point forward, given a set of criteria: a grade, gender, and name
    filter, as well as the option to randomly place a student into any branch
    if they match none naturally, and whether the branches are mutually
    exclusive (relevant if they match more than one; they will then get into
    the first one they can, replacing their other choices).

    Splitting gets somewhat complex when considering different rules for days
    for the new branch(es). You can force them to use separate days, force
    new days; minimum, maximum, and decided instances; days per instance and
    maximum instances per day. All of these are optional, and will default to
    the values from the original club if not supplied.

    TODO This has to be reimplemented as instances instead of new clubs.
    That doesn't change the parsing that much, except insofar as some of these
    variables might become redundant (e.g. force separate days = maximum
    instances per day).
    """
    if not PATH_SPLITS.exists():
        return

    with open(PATH_SPLITS, 'r') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            if not any(row):
                continue
                
            main, new, force_separate_days, mutually_inclusive, new_days, new_days_per, new_decided, new_min, new_max, new_max_per_day, randomize_unmatching, grades, genders, students = (school.normalize_club_code(c.strip()) for c in row)

            force_separate_days = bool(force_separate_days)
            mutually_exclusive = not bool(mutually_inclusive) # Hm :)
            randomize_unmatching = bool(randomize_unmatching)

            new_days = set(DAY_TO_INT[day] for day in new_days.split(';')) if new_days else None

            new_min = int(new_min) if new_min else None
            new_max = int(new_max) if new_max else None
            new_days_per = int(new_days_per) if new_days_per else None
            new_max_per_day = int(new_max_per_day) if new_max_per_day else None
            new_decided = int(new_decided) if new_decided else None

            grades = set(int(g) for g in grades.split(';')) if grades else set()
            genders = set(g.strip() for g in genders.split(';')) if genders else set()
            students = set(s.strip() for s in students.split(';')) if students else set()

            school.add_split(main, new,
                force_separate_days, new_days,
                mutually_exclusive, randomize_unmatching,
                new_min, new_max, new_days_per, new_max_per_day, new_decided,
                grades, genders, students
            )

def parse_nice_names(school: School) -> None:
    """
    Ingest the nice names file and register each one with the school.
    
    A nice name is a last-stage printing replacement for a club's name.
    It can take into account post-split names.
    """
    if not PATH_NICE_NAMES.exists():
        return

    with open(PATH_NICE_NAMES, 'r') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            if not any(row):
                continue
                
            main, nice = (c.strip() for c in row)
            school.add_nice_name(school.normalize_club_code(main), nice)

def parse_clubs(school: School):
    """
    Ingest the clubs file and register each one with the school.

    A club has a code, potentially a teacher, a set of days it can run on,
    lower and upper bounds, details about how many instances can run and how
    they must be distributed, grade and gender limitations, and a closed status
    which means no one can join it unless they are preselected.

    This is somewhat complex since it happens after merges and splits. A club
    must be checked to see whether it has been merged into another; if so,
    the absorbed row's meta does NOT replace that of the main club.
    It must also be checked to see whether it has been split into multiple;
    if so, each one must be registered, and the school's split data looked up
    to replace the meta from this row.
    """
    with open(PATH_CLUBS, 'r') as f:
        reader = csv.reader(f)
        next(reader) # Skip headers

        for row in reader:
            club_code, teacher, t, w, r, lower, upper, days_per_instance, decided_instances, min_instances, max_instances, max_instances_per_day, grades, genders, closed, _ = \
                (c.strip() for c in row)

            if not teacher:
                teacher = None

            if not lower:
                lower = 6
            if not upper:
                upper = 30
            if not min_instances:
                min_instances = 1
            if not max_instances:
                max_instances = 1
            if not days_per_instance:
                days_per_instance = 1
            if not max_instances_per_day:
                max_instances_per_day = 1

            decided_instances = int(decided_instances) if decided_instances else None

            t, w, r, closed = (bool(c) for c in (t, w, r, closed))

            if not (t or w or r):
                t, w, r = True, True, True

            lower, upper, min_instances, max_instances, days_per_instance, max_instances_per_day = \
                (int(c) for c in (lower, upper, min_instances, max_instances, days_per_instance, max_instances_per_day))

            # TODO The use of 'o' for grade should be eliminated or standardized
            grades = set((int(c) if c != 'o' else 13) for c in grades.split(';')) if grades else []
            genders = set(c.strip().upper() for c in genders.split()) if genders else []
       
            if teacher is not None:
                teacher = school.register_teacher(teacher)

            # Need to manually track this in order to discard this row
            is_absorbed = school.sanitize_club_code(club_code) in school.merges
            if is_absorbed:
                continue

            # Process each split code
            club_code = school.normalize_club_code(club_code)
            for (split_code, split_data) in school.get_all_split_codes(club_code).items():

                # Replace all this row's data with the split data
                if split_data.get('new days'):
                    new_days = split_data.get('new days')
                    t = 0 in new_days
                    w = 1 in new_days
                    r = 2 in new_days

                min_instances = split_data.get('new min instances', min_instances)
                max_instances = split_data.get('new max instances', max_instances)
                days_per_instance = split_data.get('new days per instance', days_per_instance)
                max_instances_per_day = split_data.get('new max instances per day', max_instances_per_day)
                decided_instances = split_data.get('new decided instances', decided_instances)

                # Register the club and simultaneously set the meta
                club = school.register_club(split_code)
                club.set_meta(
                    teacher, t, w, r,
                    min_instances, max_instances, days_per_instance, max_instances_per_day,
                    decided_instances,
                    lower, upper,
                    grades, genders,
                    closed
                )

                # Add mutual exclusions for splits
                if split_data and split_data['mutually exclusive']:
                    school.add_exclusion(club_code, split_code)

def parse_students(school: School):
    """
    Ingest the students file and register each one with the school.

    There are two steps here because there are two data sources that must be
    linked up. One is the survey data, which has their name and their choices
    (among other things we don't need). The other is the student linkups file
    which is generated from the master student list. This file gives us their
    grade, their gender, an alignment of their official name with the name
    they gave on the survey (which is the one we use in this program), and
    a set of the days they are unavailable for clubs, e.g. because of co-op.

    The students' choices have duplicates removed, except for Study Halls.
    Gaps are eliminated. Hence, a student who chose clubs A A B C D and is
    placed in clubs A B C is treated as getting their 1st, 2nd, 3rd choices.
    Same if they left a choice as [unchosen] or mistakenly chose [prefilled].

    However, this is not the behaviour when later removing ineligible students.
    There, the gaps are left open. TODO Consider whether to align these.
    """

    # Map of name to choices to be integrated into linkups later
    student_to_choices = {}

    with open(PATH_STUDENTS, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # Skip headers

        for row in reader:
            _, name, _, c1, c2, c3, c4, c5, _ = row

            choices_without_repeats = []
            for club_code in (school.normalize_club_code(c) for c in (c1, c2, c3, c4, c5)):
                
                # Eliminate invalid choices and repeats, except for Study Hall
                can_add = all((
                    club_code, any((
                        (club_code in {'Study Hall'}),
                        (club_code not in ['[unchosen]', '[prefilled]'] + choices_without_repeats)
                    ))
                ))

                if can_add:
                    choices_without_repeats.append(club_code)
                
                student_to_choices[name] = choices_without_repeats

    with open(PATH_LINKUPS, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # Skip headers

        for row in reader:
            _, last, first, _, grade, gender, key, exclude, days_unavailable, _ = (c.strip() for c in row)

            grade = int(grade)
            exclude = bool(exclude)
            days_unavailable = set(DAY_TO_INT[day] for day in days_unavailable.split(';')) if days_unavailable else set()

            # Exclude the student (e.g. they have left the school but are still in the system)
            if exclude:
                continue

            # No key means they didn't fill in the survey
            name = key if key else f'{first} {last}'
            choices = []

            # Add their choices (if they filled in the survey)
            if key:
                choices = student_to_choices[name]
                revised_choices = []

                for i in range(len(choices)):

                    # They may be eligible for more than one split branch
                    possible_split_codes = school.get_matching_split_codes(choices[i], name, grade, gender)
                    for code in possible_split_codes:
                        if len(revised_choices) < 5:
                            revised_choices.append(code)
                
                choices = revised_choices

            school.register_student(name, grade, gender, choices, days_unavailable)

def parse_preselects(school: School) -> None:
    """
    Ingest the preselects file and register each one with the school.

    A preselect is a placement of a student into a club before distribution.
    For example, the choir may already know which students are in it.

    A distribution carries a student's name, grade, and gender; this is because
    there have been students not on the master list, but (TODO) may be better
    done by just adding them, perhaps via another .csv that appends to linkups.

    It then carries a club code (which can be a split), the # of instances they
    will be in, and three force flags: days they must be in; days they cannot
    be in; and whether to force them in even if their schedule does not allow.
    This last is not recommended since it can prevent detecting conflicts by
    schedulers, but it can be used to override exclusions.
    """
    if not PATH_PRESELECTS.exists():
        return

    with open(PATH_PRESELECTS, 'r') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            if not any(row):
                continue

            student_name, grade, gender, club_code, n_times, forced_days, forced_nondays, force = row
            grade = int(grade)
            forced_days = set(DAY_TO_INT[d] for d in forced_days.split(';')) if forced_days else set()
            forced_nondays = set(DAY_TO_INT[d] for d in forced_nondays.split(';')) if forced_nondays else set()
            force = bool(force)
            n_times = int(n_times) if n_times else 1

            # Merges and splits; add them to each split they qualify for
            club_code = school.normalize_club_code(club_code)
            club_codes = school.get_matching_split_codes(club_code, student_name, grade, gender)
            for club_code in club_codes:

                if student_name not in school.students:
                    # print(f'Unregistered student {student_name} found in preselects')
                    school.register_student(student_name, grade, gender, [], set())

                if club_code not in school.clubs:
                    # print(f'Unregistered club {club_code} found in preselects')
                    school.register_club(club_code)

                school.add_preselect(student_name, club_code, n_times, forced_days, forced_nondays, force)

def parse_whitelists(school: School) -> None:
    """
    Ingest the whitelists file and register each one with the relevant club.

    A whitelist means that a student must be on said list to get into the club.
    If a club has even one student on its whitelist, it is in whitelist mode.

    The difference between whitelisting and preselecting (overriding) is that
    preselecting places a student into the club, whereas whitelisting leaves it
    up to them to choose the club, while turning away others who chose it.

    The students include a grade and gender in case a student is not in the
    master student list (TODO probably redundant).
    """
    if not PATH_WHITELISTS.exists():
        return

    with open(PATH_WHITELISTS, 'r') as f:
        reader = csv.reader(f)
        next(reader)

        whitelists = {}

        for row in reader:
            if not any(row):
                continue

            student_name, grade, gender, club_code = (c.strip() for c in row)
            grade = int(grade)
            club_code = school.normalize_club_code(club_code)
            possible_split_codes = school.get_matching_split_codes(club_code, student_name, grade, gender)
            for club_code in possible_split_codes:

                if student_name not in school.students:
                    # print(f'Unregistered student {student_name} found in whitelists')
                    school.register_student(student_name, int(grade), gender, [], set())

                if club_code not in school.clubs:
                    # print(f'Unregistered club {club_code} found in whitelists')
                    school.register_club(club_code)

                if club_code not in whitelists:
                    whitelists[club_code] = set()
                
                whitelists[club_code].add(student_name)

        # The school does not have a record of this. Only the clubs do...
        for (club_code, students) in whitelists.items():
            club = school.clubs[club_code]
            club.add_to_whitelist(students)

def parse_blacklists(school: School) -> None:
    """
    Ingest the blacklists file and register each one with the relevant club.

    A blacklist means that a student must NOT be on said list to get in.

    The students include a grade and gender in case a student is not in the
    master student list (TODO probably redundant).
    """
    if not PATH_BLACKLISTS.exists():
        return

    with open(PATH_BLACKLISTS, 'r') as f:
        reader = csv.reader(f)
        next(reader)

        blacklists = {}

        for row in reader:
            if not any(row):
                continue

            student_name, grade, gender, club_code = (c.strip() for c in row)
            grade = int(grade)
            club_code = school.normalize_club_code(club_code)
            possible_split_codes = school.get_matching_split_codes(club_code, student_name, grade, gender)
            for club_code in possible_split_codes:

                if student_name not in school.students:
                    # print(f'Unregistered student {student_name} found in blacklists')
                    school.register_student(student_name, int(grade), gender, [], set())

                if club_code not in school.clubs:
                    # print(f'Unregistered club {club_code} found in blacklists')
                    school.register_club(club_code)

                if club_code not in blacklists:
                    blacklists[club_code] = set()
                
                blacklists[club_code].add(student_name)

        # The school does not have a record of this. Only the clubs do...
        for (club_code, students) in blacklists.items():
            club = school.clubs[club_code]
            club.add_to_blacklist(students)

def parse_exclusions(school: School) -> None:
    """
    Ingest the exclusions file and register each one with the school.

    An exclusion between two clubs means that a student can only be in one
    of the two clubs. If they are placed in one, the system prevents them from
    being placed in the other. This is done live, but if an exclusion applies
    to a club they are preselected for, it is also checked before distribution.
    """
    if not PATH_EXCLUSIONS.exists():
        return

    with open(PATH_EXCLUSIONS, 'r') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            if not any(row):
                continue
                
            main, exclude = (school.normalize_club_code(c.strip()) for c in row)
            school.add_exclusion(main, exclude)
            school.add_exclusion(exclude, main)

def parse_input_specifications() -> dict[str, InputFile]:
    """
    Ingest the input specs file and return a dictionary of the data.
    """

    with open(PATH_INPUT_SPECS, 'r') as f:
        reader = csv.reader(f)
        next(reader)

        input_files = {}

        for row in reader:
            if not any(row):
                continue

            filename, column, datatype, example, default, notes, source = (c.strip() for c in row)
            if filename:
                f = InputFile(filename, source, notes)
                input_files[filename] = f
            
            else:
                c = InputFileColumn(column, datatype, example, default, notes)
                f.add_column(c)
    
    return input_files
