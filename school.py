from __future__ import annotations
import random
from student import Student
from club import Club
from teacher import Teacher

class School:
    """
    The main coordinator for all the data. Stores students, clubs, teachers;
    measures of the proportions of grades and genders, club repulsions
    and student reactivities (unused); and the various operations
    that manipulate clubs. The hub used to access all kinds of data.
    """
    __slots__ = ('students', 'clubs', 'teachers', 'proportions', 'repulsions', 'reactivities', 'preselects', 'merges', 'splits', 'nice_names', 'exclusions', 'splits_to_separate_days')

    students: dict[str, Student]
    clubs: dict[str, Club]
    teachers: dict[str, Teacher]

    proportions: dict[str|int, int]
    repulsions: dict[str, dict[str, int]]
    reactivities: dict[str, int]

    preselects: dict[str, tuple[str, int]]
    merges: dict[str, str]
    splits: dict[str, dict[str, dict[str, set[object]]]]
    splits_to_separate_days: dict[str, dict[str, bool]]
    nice_names: dict[str, str]
    exclusions: dict[str, set[str]]

    def __init__(self: School) -> None:
        """Initialize the school with all empty values."""
        self.students = {}
        self.clubs = {}
        self.teachers = {}

        self.proportions = {
            'M': 0,
            'F': 0,
            'O': 0,
            9: 0,
            10: 0,
            11: 0,
            12: 0,
            13: 0
        }

        self.repulsions = {}

        self.preselects = {}
        self.merges = {}
        self.splits = {}
        self.splits_to_separate_days = {}
        self.nice_names = {}
        self.exclusions = {}

    def register_club(self: School, code: str) -> Club:
        """
        Register a club with the given code if not yet registered.
        Then, return the corresponding club.
        """
        if code not in self.clubs:
            self.clubs[code] = Club(self, code)
        return self.clubs[code]

    def register_student(self: School, key: str, grade: int, gender: str, choices: list[str], days_unavailable: set[int]=set()) -> Student:
        """
        Register a student with the given key and data not yet registered.
        Then, return the corresponding student.
        """
        if key not in self.students:
            self.students[key] = Student(key, grade, gender, choices, days_unavailable)
        return self.students[key]

    def register_teacher(self: School, name: str) -> Teacher:
        """
        Register a club with the given teacher and name if not yet registered.
        Then, return the corresponding teacher.
        """
        if name not in self.teachers:
            self.teachers[name] = Teacher(name)
        return self.teachers[name]

    def add_preselect(self: School, student_name: str, club_code: str, n_times: int, forced_days: set[int], forced_nondays: set[int], force: bool=False) -> None:
        """
        Add an preselect (a preselected club) to the school registry.
        The essentials are a student name and a club code.
        It is also possible to specify a number of times (instances) to add;
        forced days that must be used; forced nondays that cannot be used;
        and a force flag that causes schedule conflicts to be ignored.

        N.B. Forcing is not recommended, because it prevents catching conflicts
        in planning. When forced, it ignores days and replaces previous clubs.
        """
        self.preselects[student_name] = self.preselects.get(student_name, []) + [(club_code, n_times, forced_days, forced_nondays, force)]

        club = self.clubs[club_code]        
        student = self.students[student_name]
        club.register_pre_student(student_name)
        student.register_pre_choice(club, n_times)

    def _sort_preselect(self: School, preselect: tuple[object]) -> list[object]:
        """
        Return a list of sort factors for preselects in order of consideration.

        Sorted prioritizing unforced (TODO why?), foreknown instances,
        fewer days per instance, fewer times per club, fewer forced nondays,
        fewer forced days.
        """
        key = []
        club_code, n_times, forced_days, forced_nondays, force = preselect
        club = self.clubs[club_code]

        key.append(force)
        key.append(club.instances_are_foreknown())
        key.append(-club.days_per_instance)
        key.append(-n_times)
        key.append(-len(forced_nondays))
        key.append(-len(forced_days))

        return key

    def get_preselected_students(self: School, club: Club) -> set[Student]:
        """
        Return the set of students who are preselected for the given club.
        """
        students = set()

        for (student_name, preselects) in self.preselects.items():
            for (club_code, n_times, forced_days, forced_nondays, force) in preselects:
                if club_code == club.code:
                    students.add(student_name)
                    break
        
        return students

    def sanitize_club_code(self: School, code: str) -> str:
        """
        Return a sanitized version of the given club code.
        """
        sanitized = ''
        for char in code:
            if char in '/:?<>\\"*|':
                sanitized += ' - '
            else:
                sanitized += char
        
        while '  ' in sanitized:
            sanitized = sanitized.replace('  ', ' ')

        return sanitized

    def normalize_club_code(self: School, code: str) -> str:
        """
        Return a sanitized and normalized version of the given club code.
        Normalizing means resolving any merges.

        TODO This would be good to combine with matching split codes.
        It just means that all club lookups have to be pluralized.
        (Or, of course, figure out splits as instances.)
        """
        code = self.sanitize_club_code(code)

        if code in self.merges:
            return self.merges[code]

        return code

    def get_matching_split_codes(self: School, code: str, name: str, grade: int, gender: str) -> set[str]:
        """
        Return a set of the matching split codes for the given course
        for the given student identified by name, grade, and gender;
        i.e., for all splits of the given course code, narrow them to the ones
        that the student is eligible for. If they are not eligible for any,
        an optional flag allows them to be placed in a random branch.
        """

        if code not in self.splits:
            return [code]
        else:
            options = []

            # For randomizing unmatching
            unmatching_options = []

            for (new, data) in self.splits[code].items():

                matches_name = (not data['students']) or (name in data['students'])
                matches_grade = (not data['grades']) or (grade in data['grades'])
                matches_gender = (not data['genders']) or (gender in data['genders'])

                if (matches_name and matches_grade and matches_gender):
                    options.append(new)

                if data['randomize unmatching']:
                    unmatching_options.append(new)

            # Randomize those who have nowhere else to go
            if not options:
                options = unmatching_options

            random.shuffle(options)
            return set(options)

    def get_all_split_codes(self: School, code: str) -> dict[str, dict[str, int|None]]:
        """
        Return a dictionary of the split codes for the given course code.
        The dictionary maps the original code to a subdictionary whose keys
        are branch names and whose values are a dictionary of split parameters.

        Remove the original branch.

        TODO This can certainly be organized better.
        """
        variants = {code: {}}
        
        if code in self.splits:
            for new in self.splits[code]:
                variants[new] = self.splits[code][new]
            
            del variants[code]

        return variants

    def get_all_clubs_for_code(self: School, code: str) -> set[Club]:
        """
        Return a set of all the clubs for the given code after accounting
        for possible splits.
        """
        return set(self.clubs[split] for split in self.get_all_split_codes(code))

    def add_merge(self: School, main: str, absorb: str) -> None:
        """
        Add the given merge to the registry. A merge consists of a main club
        and a club that is absorbed into it. The main club will always be
        substituted for the absorbed club.
        """
        self.merges[absorb] = main

    def add_split(self: School, main: str, new: str,
            force_separate_days: bool, new_days: set[int]|None,
            mutually_exclusive: bool, randomize_unmatching: bool,
            new_min: int|None, new_max: int|None, new_days_per: int|None, new_max_per_day: int|None, new_decided: int|None,
            grades: set[int], genders: set[str], students: set[str]
        ) -> None:
        """
        Add the given split to the registry.
        A split primarily consists of a main club and a new branch name.
        It also has the possibility of forcing separate days from the original
        branch, being mutually exclusive with the other branches, randomizing
        the branch for students who are ineligible for any, and optionally
        replacing all scheduling information. (These last keys are only added
        to the dictionary if supplied; otherwise, the original branch's
        scheduling information will be retained.)

        TODO Worth explicitly taking the original branch's info rather than
        leaving key presence uncertain? But requires being able to look it up.
        """

        new = self.normalize_club_code(new)
        
        if main not in self.splits:
            self.splits[main] = {}

        # Remove the original branch
        if main in self.clubs:
            del self.clubs[main]

        # Register the essential options for the new branch
        self.splits[main][new] = {
            'grades': grades, 'genders': genders, 'students': students,
            'force separate days': force_separate_days,
            'mutually exclusive': mutually_exclusive, 'randomize unmatching': randomize_unmatching
        }

        # Add optional keys
        if new_days is not None:
            self.splits[main][new]['new days'] = new_days
        if new_min is not None:
            self.splits[main][new]['new min instances'] = new_min            
        if new_max is not None:
            self.splits[main][new]['new max instances'] = new_max            
        if new_days_per is not None:
            self.splits[main][new]['new days per instance'] = new_days_per            
        if new_max_per_day is not None:
            self.splits[main][new]['new max instances per day'] = new_max_per_day            
        if new_decided is not None:
            self.splits[main][new]['new decided instances'] = new_decided
        
        # Record of whether the split requires a separate day for this main
        # This is used when clubs are checking scheduling possibilities for
        # new instances, in the event that a new instance could be on a day
        # that ended up being distributed to a split.

        # TODO This is pretty messy, and doesn't really make sense.
        # Why should the other branches' force separate days setting matter?
        # For any given branch, if IT uses separate days, that's what counts

        if new not in self.splits_to_separate_days:
            self.splits_to_separate_days[new] = {}
        self.splits_to_separate_days[new][main] = force_separate_days

    def add_nice_name(self: School, club_code: str, nice_name: str) -> None:
        """
        Register the given nice name for the given club code.
        """
        self.nice_names[club_code] = nice_name

    def get_nice_name(self: School, club: Club) -> str:
        """
        Return the nice name for the given club (its code
        if no nice name has been registered).
        """
        return self.get_nice_name_from_code(club.code)

    def get_nice_name_from_code(self: School, code: str) -> str:
        """
        Return the nice name for the given club code (the same code
        if no nice name has been registered).
        """
        return self.nice_names.get(code, code)

    def filter_split_days(self: School, club: Club, days: set[int]) -> set[int]:
        """
        Return the given set of days, after filtering out split days.

        This means that if the club has any other branches, and the branches
        are flagged to use separate days, eliminate any days that are in use
        by the other branches.
        """
        if club.code not in self.splits_to_separate_days:
            return days

        # TODO This model doesn't make sense, as noted in add_split
        for (other_code, force_separate_days) in self.splits_to_separate_days[club.code].items():
            peer_codes = set(self.get_all_split_codes(other_code)).difference({club.code})
            for peer_code in peer_codes:
                other_club = self.clubs[peer_code]
                days = days.difference(other_club.taken_days())

        return days

    def add_exclusion(self: School, code_a: str, code_b: str) -> None:
        """
        Add the given pair of club codes to the registry of exclusions.
        All exclusions are mutual, so they are added bidirectionally.
        """
        self.exclusions[code_a] = self.exclusions.get(code_a, set()).union({code_b})
        self.exclusions[code_b] = self.exclusions.get(code_b, set()).union({code_a})

    def tally_votes(self: School) -> None:
        """
        Calculate the votes each club received (both choices & preselections).
        """
        for club in self.clubs.values():
            club.reset_votes()

        for student in self.students.values():
            for (key, code) in student.choices.items():
                self.clubs[code].add_vote(key)
            for code in student.pres:
                self.clubs[code].add_pre_vote()

    def remove_students_who_arent_eligible(self: School) -> None:
        """
        Go through all the students and unregister any club choices for which
        they are not eligible.
        """
        for student in self.students.values():
            for club_code in student.choices.copy().values():
                if not self.clubs[club_code].is_student_eligible(student):
                    student.unregister_choice(club_code)
    
    def remove_clubs_that_cannot_run(self: School) -> None:
        """
        Go through all the clubs and unregister any that will not run.
        Also unregister such clubs as choices for students who chose them.
        """
        for club in self.clubs.copy().values():
            if not club.can_run():
                del self.clubs[club.code]
                for student in self.students.values():
                    student.unregister_choice(club.code)

    def calculate_proportions(self: School) -> None:
        """
        Calculate the proportions of grades and genders for all the students,
        and save them to the proportions dictionary. Proportions are decimals
        between 0 and 1 representing percentages.
        """
        n = len(self.students)
        for s in self.students.values():
            self.proportions[s.grade] += 1
            self.proportions[s.gender] += 1
        
        for (k, v) in self.proportions.items():
            self.proportions[k] = v / n

    def calculate_repulsions(self: School) -> None:
        """
        Calculate the repulsion factor for each club to each other club,
        and save them to a dictionary whose keys are club codes and whose
        values are subdictionaries mapping other club codes to repulsion
        factors. Also save each club's subdictonary to itself.

        TODO The last part is redundant, as noted in Club.

        A club's repulsion factor is a measure of how often it co-occurs,
        and at what priority of choice, with a given other club. It also
        has a total repulsion factor indicating its total co-occurrence.
        Pracically speaking, two clubs with a high repulsion factor should not
        share a day, since many students hope to get into both.
        """

        self.repulsions = {key: {} for key in self.clubs}

        for student in self.students.values():
            all_choices = set()

            # For each choice...
            for i in range(1, 6):
                a = student.choices.get(i, None)
                if not a:
                    continue

                # For each other choice...
                for j in range(i + 1, 6):
                    b = student.choices.get(j, None)
                    if not b:
                        continue

                    # Add both to all choices to compare with preselects later
                    all_choices.add(a)
                    all_choices.add(b)

                    # Weight by how high the choices are in their list
                    n = (6 - i) * (6 - j)
                    self.repulsions[a][b] = self.repulsions[a].get(b, 0) + n
                    self.repulsions[b][a] = self.repulsions[b].get(a, 0) + n

            # Preselects are considered conflicting with all other choices
            # (High value -- TODO review -- because the odds are 100%)
            for a in student.pres:
                for b in all_choices:
                    self.repulsions[a][b] = self.repulsions[a].get(b, 0) + 10
                    self.repulsions[b][a] = self.repulsions[b].get(a, 0) + 10
        
        # Sum and add a total; also save to the individual club (redundant)
        for a in self.repulsions:
            self.repulsions[a]['_total'] = sum(self.repulsions[a].values())
            self.clubs[a].repulsions = self.repulsions[a]

    def calculate_reactivities(self: School) -> None:
        """
        Calculate the reactivity factor for each student, and save them
        to a dictionary whose keys are student names and whose values are
        the reactivity factors. Also save each student's factor to itself.

        A student's reactivity is a measure of how popular the student's club
        choices are, and specifically how overfull they are. The more overfull
        a student's choice, the higher the chance that it will come to their
        2nd, 3rd, 4th, 5th choices. Practically speaking, this means we should
        give them a chance to get into said choices before students who are
        likely to get their higher choices.

        TODO This does not yield good scores when distributing students;
        revisit the concept.

        TODO Clubs that are not overfull contribute negative reactivity,
        which is not intended.
        """
        self.reactivities = {key: {} for key in self.students}
        for student in self.students.values():
            reactivity = 0

            # Go through each choice
            for i in range(1, 6):
                code = student.choices.get(i, None)
                if not code:
                    continue
            
                # Compare the votes at different priorities to the limit
                # TODO Improve algorithm. Should it really be weighted?
                club = self.clubs[code]
                limit = club.days_per_instance * (club.decided_instances if (club.decided_instances is not None) else 1)
                reactivity += (6 - i) * (club.votes['123'] - limit)
                reactivity += (6 - i) * ((club.votes['12345'] - limit) // 2)
            
            # Save both to own dictionary and to student
            student.reactivity = reactivity
            self.reactivities[student.name] = reactivity
