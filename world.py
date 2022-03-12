from __future__ import annotations
import random

from report import Report
from club import Club
from student import Student

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from school import School

class World:
    """
    Represents a distribution of clubs to days and students to clubs.
    Also keeps a report of the state of the distribution. This is because
    the clubs and students in it are not stable and can be reset later.
    """
    __slots__ = ['school', 'clubs', 'students', 'report']

    school: School
    clubs: list[Club]
    students: list[Student]
    report: Report
    
    def __init__(self: World, school: School, clubs: list[Club], students: list[Student]) -> None:
        """
        Initialize this world with the given school, clubs, and students,
        and a blank report.
        """
        self.school = school
        self.clubs = clubs
        self.students = students
        self.report = Report(self.clubs, self.students)
    
    def distribute(self: World) -> None:
        """
        Distribute the students into their preselected and chosen clubs.
        Fill leftover spots, balance club instances, and save the report.
        """
        self.distribute_preselects()
        self.distribute_choices()
        self.distribute_leftovers()

        for club in self.clubs:
            club.balance_instances_on_same_day()

        self.report.populate_world_distribution(self.school, self.clubs, self.students)

    def distribute_preselects(self: Report) -> None:
        """
        Carry out all the preselects; that is, place preselected students
        into the clubs they are preselected for.
        """
        for (student_name, preselects) in self.school.preselects.items():
            preselects = sorted(preselects, key=self.school._sort_preselect)

            # Place each student into each of their preselects each of the times
            for (club_code, n_times, forced_days, forced_nondays, force) in preselects:
                student = self.school.students[student_name]
                club = self.school.clubs[club_code]

                for _ in range(n_times):
                    result = club.add_student(student, force=force, forced_days=forced_days, forced_nondays=forced_nondays)

                    # Debugging / catching conflicts in planning
                    if not result:
                        print(f'Could not preadd {student.name} to {club.code}')

    def distribute_choices(self: Report) -> None:
        """
        Distribute students into clubs by giving them their choices.
        Start in a random order (TODO improvable?) and give them a choice --
        if not their 1st, their 2nd, and so on, until they get one that round.
        For each remaining round, sort them according to who has gotten
        the fewest choices so far.
        """
        random.shuffle(self.students)

        # These sort orders seem to make it worse
        # self.students.sort(key=lambda s: s.reactivity)
        # self.students.sort(key=lambda s: len(s.free_days()))

        successes = {s.name: [] for s in self.students}

        # Maximum of 5 choices = 5 rounds
        for _ in range(5):
            for s in self.students:

                # Continually try to give them their next highest choice
                # until they either get one or run out of choices
                club_code = s.get_next_choice()
                success = False
                while not success and club_code is not None:
                    club = self.school.clubs.get(club_code)

                    # Try to add them; add success or failure to the sort order
                    success = club.add_student(s)
                    successes[s.name].append(success)

                    # If failed, try the next highest choice until we run out
                    if not success:
                        club_code = s.get_next_choice()

            # For fairness, alternate direction
            self.students.reverse()
            self.students.sort(key=lambda s: successes[s.name])

            # This sort order is not as good
            # self.students.sort(key=lambda s: s.choices_gotten_score)

    def distribute_leftovers(self: Report) -> None:
        """
        Distribute all students who have free days left by placing them
        in Study Halls.
        """

        for student in self.students:
            while student.free_days():
                club = self.school.clubs['Study Hall']
                club.add_student(student)

    def score(self: World) -> int:
        """
        Return this world's score (as calculated by its report).
        Only makes sense between distribution and resetting.
        """
        return self.report.calculate_score()

    def _validate_clubs(self: World) -> tuple[bool, str]:
        """
        Validate this world's clubs. Return a tuple of (validity, message).
        The message indicates the first validity test that failed.
        """
        for club in self.clubs:
            instances = self.report.clubs[club.code]

            if len(instances) > club.max_instances:
                return False, 'Club with more than max instances'
            
            if len(instances) < club.min_instances:
                return False, 'Club with fewer than min instances'

            if (club.decided_instances is not None) and (len(instances) != club.decided_instances):
                return False, 'Club with fewer or more than decided instances'

            for (instance_key, data) in instances.items():
                
                if len(data['days']) != club.days_per_instance:
                    return False, 'Club with wrong days per instance'

                if data['days'].difference(club.pre_days):
                    return False, 'Club with instances on impossible days'

                if (club.decided_instances is None) and (len(data['students']) < club.lower):
                    return False, 'Club with too few students'
                
                if len(data['students']) > club.upper:
                    return False, 'Club with too many students'
                
                if club.genders:
                    for student_name in data['students']:
                        if self.school.students[student_name].gender not in club.genders:
                            return False, 'Club with students of the wrong gender'     

                if club.grades:                    
                    for student_name in data['students']:
                        if self.school.students[student_name].grade not in club.grades:
                            return False, 'Club with students of the wrong grade'

                if club.whitelist:                    
                    for student_name in data['students']:
                        if student_name not in club.whitelist:
                            return False, 'Club with students not on the whitelist'

                if club.blacklist:                    
                    for student_name in data['students']:
                        if student_name not in club.blacklist:
                            return False, 'Club with students on the blacklist'

                if club.excluded_students:                    
                    for student_name in data['students']:
                        if student_name in club.exclusions:
                            return False, 'Club with students excluded for having been in other clubs'

                if club.closed:
                    preselected = self.school.get_preselected_students(club)
                    if data['students'].difference(preselected):
                        return False, 'Closed club with non-preselected students'
        
        return True, 'Valid'

    def _validate_students(self: World) -> tuple[bool, str]:
        """
        Validate this world's students. Return a tuple of (validity, message).
        The message indicates the first validity test that failed.
        """
        for student in self.students:
            for (day, club_code) in self.report.students[student.name]['days'].items():
                if club_code not in set(student.choices.values()).union(student.pres.keys()).union({'Study Hall'}):
                    return False, 'Student in a club they did not pick nor were preselected nor was Study Hall'

        return True, 'Valid'   
    
    def _validate_preselects(self: World) -> tuple[bool, str]:
        """
        Validate this world's preselects. Return a tuple of (validity, message).
        The message indicates the first validity test that failed.
        """
        for (student_name, preselects) in self.school.preselects.items():
            days = self.report.students[student_name]['days']

            for (club_code, n_times, forced_days, forced_nondays, force) in preselects:
                club = self.school.clubs[club_code]
                
                if list(days.values()).count(club_code) < (n_times * club.days_per_instance):
                    return False, 'Student not in preselected club enough times'

                for day in forced_days:
                    if days[day] != club_code:
                        return False, 'Student in preselcted club on a day that was not a forced day'
                
                for day in forced_nondays:
                    if days[day] == club_code:
                        return False, 'Student in preselcted club on a forced nonday'

        return True, 'Valid'

    def validate(self: World) -> tuple[bool, str]:
        """
        Validate this world. Return a tuple of (validity, message).
        The message indicates the first validity test that failed.
        """
        validators = (self._validate_clubs, self._validate_students, self._validate_preselects)
        for validator in validators:
            result, msg = validator()
            if not result:
                return result, msg

        return True, 'Valid'        

    def __repr__(self: World) -> str:
        """
        Return a string representation of this world (its score).
        """
        return f'{self.score}'
