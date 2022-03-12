from __future__ import annotations
import itertools
from math import inf
import math
import random
from club_instance import ClubInstance
from teacher import Teacher

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from student import Student
    from school import School

class Club:
    """
    Represents a club option. Identified by a code. May have a teacher set.

    The pre-chosen options for days, minimum and maximum number of instances
    (groups of students), number of days each instance requires, and maximum
    instances per day all affect scheduling.

    A club can also keep track of its lower and upper bounds, grade and gender
    limitations, pre-selected and priority students, whitelist and blacklist,
    closed or open status, and students excluded for being in other clubs.

    A club tallies its votes. This is a count of how many times it has appeared
    as a given choice in student's list of choices.

    A club has a repulsion factor pairwise with every other club. This number
    represents how often it is co-chosen with the other club, and hence how
    much it should be "repelled" from appearing on the same day as the other,
    lest a student only be able to get into one.
    """
    __slots__ = (
        'school',
        'code', 'teacher',
        'min_instances', 'max_instances', 'days_per_instance', 'max_instances_per_day',
        'decided_instances',
        'pre_days', 'days_used_counts',
        'lower', 'upper', 
        'instances', 'votes',
        'grades', 'genders',
        'prelist', 'priority_list', 'whitelist', 'blacklist',
        'closed', 'excluded_students',
        'repulsions')

    school: School
    code: str
    teacher: Teacher|None
    pre_days: set[int]
    votes: dict[int|str, int]
    lower: int
    upper: int
    min_instances: int
    max_instances: int
    days_per_instance: int
    max_instances_per_day: int
    decided_instances: int|None
    instances: dict[str, ClubInstance]
    days_used_counts: dict[int, int]
    grades: set[int]
    genders: set[str]
    prelist: set[str]
    whitelist: set[str]
    blacklist: set[str]
    excluded_students: set[str]
    priority_list: set[str]
    closed: bool
    repulsions: dict[str, int]
    
    def __init__(self: Club, school: School, code: str) -> None:
        """Initialize this Club. Leave metadata empty for now."""
        self.school = school
        self.code = code
        self.excluded_students = {}
        self.repulsions = {}
        self.instances = {}
        self.days_used_counts = {}

        # Meta to be set later
        self.teacher = None
        self.lower = 6
        self.upper = 30
        self.prelist = set()
        self.pre_days = set()
        self.min_instances = 1
        self.max_instances = inf
        self.days_per_instance = 1
        self.max_instances_per_day = 1
        self.decided_instances = None
        self.grades = set()
        self.genders = set()
        self.whitelist = set()
        self.blacklist = set()
        self.priority_list = set()
        self.closed = False

    def add_pre_vote(self: Club) -> None:
        """Register the fact that this club was pre-selected for a student."""
        self.votes['pre'] += 1
        self.votes['weighted'] += 5

    def add_vote(self: Club, key: int) -> None:
        """Register the fact that this club was a student's keyth choice."""
        self.votes[key] = self.votes.get(key, 0) + 1
        self.votes['12345'] += 1
        self.votes['123'] += (key < 4)
        self.votes['weighted'] += (6 - key)

    def reset_votes(self: Club) -> None:
        """Untally all added votes so they can be recalculated."""
        self.votes = {
            'pre': 0,
            '123': 0,
            '12345': 0,
            'weighted': 0
        }

        for key in range(1, 6):
            self.votes[key] = 0

    def can_run(self: Club) -> bool:
        """
        Return True iff this club can run. If not, this can be because
        its votes are too low to make an instance, or because human wisdom
        has decided on running 0 instances in the spreadsheet.

        N.B. Does not take into account min and max instances or available days
        because it is assumed that the data ingested is basically valid.
        TODO But we could allow for a default 0 instead of 1 min instances
        and then use the first check reasonably.
        """        

        if self.decided_instances is None:
            return (self.closed) or (self.votes[1] >= self.lower)
        else:
            return self.decided_instances > 0

    def day_is_available(self: Club, day: int) -> bool:
        """
        Return True iff the given day is available for a new instance.
        A day is available if it's one of the club's possible days,
        the club's teacher is not engaged that day, and no day has more
        than the maximum number of groups on it.
        """
        return all((
            (day in self.pre_days),
            (self.teacher is None) or (self.teacher.is_day_free(day)),
            (self.days_used_counts.get(day, 0) < self.max_instances_per_day)
        ))

    def available_days(self: Club) -> set[int]:
        """
        Return the set of available days. Days are 0-indexed from Tuesday.
        """
        base = set(filter(lambda i: self.day_is_available(i), self.pre_days))
        return self.school.filter_split_days(self, base)

    def taken_days(self: Club) -> set[int]:
        """
        Return the set of days used by all instances of this club.
        """
        days = set()
        for i in self.instances.values():
            days = days.union(i.days)
        return days

    def register_pre_student(self: Club, student_name: str) -> None:
        """
        Add the given student name to the set of students who are preselected.
        """
        self.prelist.add(student_name)

    def register_priority_student(self: Club, student_name: str) -> None:
        """
        Add the given student name to the set of students who should be given
        priority when joining.

        TODO This currently does nothing.
        """
        self.priority_list.add(student_name)

    def set_meta(self: Club, teacher: Teacher|None,
            t: bool, w: bool, r: bool,
            min_instances: int, max_instances: int, days_per_instance: int, max_instances_per_day: int, 
            decided_instances: int|None,
            lower: int, upper: int, 
            grades: set[int], genders: set[str],
            closed = bool) -> None:
        """
        Set all the metadata for this club.

        T, W, R are interpreted as 0, 1, 2 for the zero-indexed day system.
        A specific number of decided instances overrules minimum and maximum.   
        """

        # Clubs do not need to have specific teachers
        if teacher is not None:
            self.teacher = teacher
            teacher.add_club(self)

        self.lower = lower
        self.upper = upper
        self.grades = grades
        self.genders = genders
        self.closed = closed

        # Interpret T, W, R as zero-indexed days
        self.pre_days = set()
        for (i, flag) in enumerate((t, w, r)):
            if flag:
                self.pre_days.add(i)
        
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.days_per_instance = days_per_instance
        self.max_instances_per_day = max_instances_per_day
        self.decided_instances = decided_instances

        # Align minimum and maximum instances with decided for simplicity
        if self.decided_instances is not None:
            self.min_instances = self.max_instances = self.decided_instances

    def add_to_whitelist(self: Club, names: set[str]) -> None:
        """
        Add the given set of student names to the whitelist for this club.
        If a club has a whitelist, any students NOT on it may not join.
        """
        self.whitelist = self.whitelist.union(names)

    def add_to_blacklist(self: Club, names: set[str]) -> None:
        """
        Add the given set of student names to the blacklist for this club.
        If a club has a blacklist, any students ON it may not join.
        """
        self.blacklist = self.blacklist.union(names)

    def remove_instance(self: Club, instance: ClubInstance) -> None:
        """
        Remove the given instance from this club.
        Untally its contribution to our count of days used.
        Remove the record of its being used from our teacher, if we have one.
        """
        del self.instances[instance.key]

        for day in instance.days:
            if day in self.days_used_counts:

                # Not really a necessary distinction
                if self.days_used_counts[day] == 0:
                    del self.days_used_counts[day]
                else:
                    self.days_used_counts[day] -= 1

            if self.teacher is not None:
                self.teacher.reset_day(day)

    def reset_student_distribution(self: Club) -> None:
        """
        Reset all records of students who have been placed in this club.
        NOTE: Does not remove it on student side. The caller must do so.

        Any instances that were added not during world generation but in order
        to accommodate more students will be deleted. The others will have
        their list of students cleared.

        Exclusions are also forgotten, since they are tracked as a byproduct
        of distribution of students.

        TODO This behaviour may need to change; technically, THIS club having
        its student distribution reset does not mean the clubs the excluded
        students were in had their student distributions reset!
        """
        for key in self.instances.copy():
            i = self.instances[key]
            if i.expanded:
                self.remove_instance(i)
            else:
                i.reset_students()

        self.re_key_instances()
        self.excluded_students = set()

    def reset_entire_distribution(self: Club) -> None:
        """
        Reset/remove all records of students and instances in this club.
        NOTE: Does not remove anything on student side. The caller must do so.
        """
        self.reset_student_distribution()

        for key in self.instances.copy():
            i = self.instances[key]
            self.remove_instance(i)

        self.re_key_instances()

    def _next_instance_key(self: Club, offset: int=0) -> str:
        """
        Return the next instance key to be created. It is the next letter of
        the alphabet after the last one currently used. (Thanks to instance
        rekeying, they are always contiguous.)

        TODO No plan in place for more than 26 instances.
        """
        return chr(65 + len(self.instances) + offset)

    def create_instance(self: Club, days: set[int], expanded: bool=False) -> ClubInstance:
        """
        Create a new instance of this club on the given day(s).
        Mark whether this is a creation through expansion.
        """
        key = self._next_instance_key()
        instance = ClubInstance(self, key, days, expanded)
        self.instances[key] = instance

        # Add to day used counts
        for day in days:
            self.days_used_counts[day] = self.days_used_counts.get(day, 0) + 1

        # Set used on teacher side
        if self.teacher is not None:
            self.teacher.take_days(days)

        # print(f'for {self.code} created instance on days {days}')
        return instance

    def _get_least_repulsive_instance(self: Club, student: Student, options: tuple[ClubInstance]=tuple(), force: bool=False, forced_days: set[int]=set(), forced_nondays: set[int]=set()) -> ClubInstance:
        """
        Return the instance that has the least repulsion with the student.
        Instance-student repulsion, explained in the instance's method docs,
        measures how many choices the student would lose out on if they were
        added to the instance.

        Options contains the instances to consider. If not supplied, they are
        instead determined on the fly, limited by the various force prameters.
        """
        if not options:
            options = self._get_instance_options(student, force, forced_days, forced_nondays)

        # Short-circuit
        if len(options) == 1:
            return options[0]

        # Shuffle (for equal sorts) and sort by repulsion, ascending
        options = list(options)
        random.shuffle(options)
        options.sort(key=lambda o: o.repulsion(student))

        return options[0]

    def _get_instance_options(self: Club, student: Student, force: bool=False, forced_days: set[int]=set(), forced_nondays: set[int]=set()) -> tuple[ClubInstance]:
        """
        Return a tuple of the instances in this club that the student can join.

        Forced days: the student must join an instance on these days.
        Forced nondays: the student cannot join an instance on these days.
        Force: ignore whether the student has the day free. In this case,
        the student's choice may be preselected. Still respects (non)days.
        
        TODO How does this last combine with students having unavailable days
        for the purposes of mentorship, for instance?

        TODO This last one is not currently handled well on the student side.
        Specifically, choices gotten can't handle erasing existing choices.
        """
        
        def _days_filter(i: ClubInstance) -> set[int]:
            """
            Return the set of days in the given instance that also respect
            the forced days and forced nondays limitations.
            """
            days = i.days
            if forced_days:
                days = days.intersection(forced_days)
            return days.difference(forced_nondays)

        # Filter by instances that match the required days and nondays
        valid_instances = tuple(filter(_days_filter, self.instances.values()))

        # Filter by instances the student is not already in (even if forced!)
        valid_instances = tuple(filter(lambda i: student not in i.students, valid_instances))

        # Only check if the student can actually be added if not forcing
        if force:
            return tuple(valid_instances)
        else:
            return tuple(filter(lambda i: i.can_add_student(student), valid_instances))

    def exclude_student(self: Club, student: Student) -> None:
        """
        Add the given student's name to our exclusion list (because they have
        joined a club that is exclusive with ours).
        """
        self.excluded_students.add(student.name)

    def _try_to_expand_instances(self: Club, student: Student, force: bool=False, forced_days: set[int]=set(), forced_nondays: set[int]=set()) -> tuple[bool, ClubInstance|None]:
        """
        Try to expand this club's instances to accommodate another student.
        Return the result as a boolean, and the new instance or None if failed.
        Fail if there are not enough usable days to create a new instance.
        """
        
        # Already more instances than the max?
        if len(self.instances) >= self.max_instances:
            return False, None
        
        # Not enough usable days for a new instance?
        usable_days = self.available_days()
        
        # Narrow down the usable days
        usable_days = usable_days.difference(forced_nondays)
        if forced_days:
            usable_days = usable_days.intersection(forced_days)

        if not force:
            usable_days = usable_days.intersection(student.free_days())

        # Fail if not enough
        if len(usable_days) < self.days_per_instance:
            return False, None

        # Welp, looks like we can make one that the student can get into!
        options = []
        
        # For each set of days, depending on how many we need for an instance,
        # create a temporary instance to be considered for expansion
        
        # TODO This is the 3rd or 4th time writing this logic; refactor!

        if self.days_per_instance == 3:
            options.append(ClubInstance(self, f'expand-0', usable_days.copy(), True))

        elif self.days_per_instance == 2:
            for (i, pair) in enumerate(itertools.pairwise(usable_days)):
                options.append(ClubInstance(self, f'expand-{i}', set(pair), True))
        
        elif self.days_per_instance == 1:
            for (i, day) in enumerate(usable_days):
                options.append(ClubInstance(self, f'expand-{i}', {day}, True))

        instance = self._get_least_repulsive_instance(student, options, force, forced_days, forced_nondays)

        # Fully create the instance the instance to ourselves
        self.create_instance(instance.days, True)

        return True, instance

    def add_student(self: Club, student: Student, force: bool=False, forced_days: set[int]=set(), forced_nondays: set[int]=set()) -> bool:
        """
        Add the given student to this club, if possible. Return True iff
        the operation succeeds. It will fail if there are no instances
        with days the student can join.

        1. Check mutual exclusions with other clubs.
        2. Limit options based on the days the student is forced to use or not
           use, if any.
        3. If there are any, 
        """

        # Prevent students who are in a mutually exclusive club, unless forced
        if (not force) and (student.name in self.excluded_students):
            return False

        # Are there options?
        options = self._get_instance_options(student, force, forced_days, forced_nondays)        
        if options:

            # Add the student
            instance = self._get_least_repulsive_instance(student, options, force)
            instance.add_student(student)

            # Register exclusions with other clubs
            if self.code in self.school.exclusions:
                for other_code in self.school.exclusions[self.code]:
                    for other_club in self.school.get_all_clubs_for_code(other_code):
                        other_club.exclude_student(student)

            return True

        else:

            # Try to expand our instances
            did_expand, instance = self._try_to_expand_instances(student, force, forced_days, forced_nondays)                
            if not did_expand:
                return False

            else:
                # Try to add the student
                success = self.add_student(student, force, forced_days, forced_nondays)

                # If it didn't succeed anyway, remove the expanded instance
                if not success:
                    self.remove_instance(instance)

                return success

    def is_student_eligible(self: Club, student: Student) -> bool:
        """
        Return True iff the given student can join this club.

        1. Yes if they are preselected.
        2. No if they are not preselected and the club is closed-membership.
        3. The student is on the whitelist, if there is one.
        4. The student is not on the blacklist, if there is one.
        5. The student's grade matches the requirements, if any.
        6. The student's gender matches the requirements, if any.
        7. The student is not in any club that excludes membership in this one.
        """
        if student.name in self.prelist:
            return True
        if self.closed and (student.name not in self.prelist):
            return False

        if self.whitelist and (student.name not in self.whitelist):
            return False
        if self.blacklist and (student.name in self.blacklist):
            return False
        
        if self.grades and (student.grade not in self.grades):
            return False
        if self.genders and (student.gender not in self.genders):
            return False

        # If they are in any preset club that excludes us, they aren't eligible for us
        for choice_code in student.choices.values():
            if choice_code in self.school.exclusions:
                if self.code in self.school.exclusions[choice_code]:
                    for club in self.school.get_all_clubs_for_code(choice_code):
                        if club.instances_are_foreknown():
                            return False

        return True

    def instances_are_foreknown(self: Club) -> bool:
        """
        Return True iff the number and days of this club's planned instances
        are such that there is no flexibility in the days it will have.

        For example, a club that must run once, uses one day per instance,
        and is only offered on Thurs has its instances foreknown.
        But a club that can run more than once, uses one day per instance,
        and could be offered on Tues, Wed, or Thurs would return False.
        """
        return (len(self.pre_days) * self.max_instances_per_day) <= (self.min_instances * self.days_per_instance)

    def _sets_of_taken_days(self: Club) -> list[set[int]]:
        """
        Return a list of sets of days occupied by this club's instances.

        TODO This logic has been implemented more than once.
        """
        sets_of_days = []
        taken_days = self.taken_days()

        if self.days_per_instance == 3:
            sets_of_days.append(taken_days)

        elif self.days_per_instance == 2:
            for pair in itertools.pairwise(taken_days):
                sets_of_days.append(set(pair))

        elif self.days_per_instance == 1:
            for day in taken_days:
                sets_of_days.append({day})
        
        return sets_of_days

    def balance_instances_on_same_day(self: Club) -> None:
        """
        For any instances that share a set of days, balance out the students
        among them. Also rekey the instances and discard any unnecessary
        instances after shuffling their students to others.

        Example: 90 students in 5 Study Hall instances on the same day.
        If Study Hall has a max of 25, we need 4 instances = ceil(90 / 25).
        Each instance should have a max of 23 students in it (90 / 4).
        Distribute the students into 4 instances and discard the other one.

        TODO Students are distributed randomly, but could be strategic.
        """

        # For each set of days taken in this club, get matching instances
        for set_of_days in self._sets_of_taken_days():                
            instances = list(filter(lambda i: i.days == set_of_days, self.instances.values()))
            if len(instances) < 2:
                continue
            
            # Clear existing students from the instances
            students = set()
            for i in instances:
                students = students.union(i.students)
                i.students = set() # "Danger, baby, love's gonna leave!"
            
            n_students = len(students)
            n_ideal_instances = math.ceil(n_students / self.upper)

            # Deal students into the instances that will be kept
            # TODO This is what could be non-random in future
            random.shuffle(instances)
            for (i, student) in enumerate(students):
                instances[i % n_ideal_instances].students.add(student)

            # Delete excess instances
            for instance in instances[n_ideal_instances:]:
                self.remove_instance(instance)
        
        self.re_key_instances()

    def re_key_instances(self: Club) -> None:
        """
        Take this club's instances, sort them by the days they use,
        and assign each one a new key.
        This eliminates potential gaps after removing instances.
        """
        instances = sorted(self.instances.values(), key=lambda i: sorted(i.days))
        self.instances = {}
        for (i, instance) in enumerate(instances):
            key = self._next_instance_key()
            instance.key = key
            self.instances[key] = instance

    def get_ideal_n_instances(self: Club) -> int:
        """
        Return the number of instances that could be run based on the votes
        for this club and the limitations on instance count and size.
        """
        # base = min(self.max_instances, self.votes[0] // self.upper)
        base = math.ceil(self.votes['123'] / self.upper)
        refined = max(self.min_instances, base)
        return min(refined, self.max_instances_per_day * len(self.pre_days))

    def repulsion(self: Club, other: Club) -> int:
        """
        Return the repulsion factor between this club and the other club.

        TODO This is probably just redundant storage; can be looked up
        based on the school's record.
        """
        return self.repulsions[other.code] if other.code in self.repulsions else 0

    def mixedness(self: Club, expected: dict[object, float]) -> tuple[float]:
        """
        Return a tuple of the scores for mixedness of grade and gender.
        A club's mixedness scores are the average of all its instances.
        """
        mixed_grades = []
        mixed_genders = []

        for instance in self.instances.values():
            mixed_grade, mixed_gender = instance.mixedness(expected)
            mixed_grades.append(mixed_grade)
            mixed_genders.append(mixed_gender)
        
        return sum(mixed_grades) / len(mixed_grades), sum(mixed_genders) / len(mixed_genders)

    def __repr__(self: Club) -> str:
        """Return a string representation of this club (its code)."""
        return self.code

    def __hash__(self: Club) -> int:
        """Return a has value of this club (a hash of its code)."""
        return hash(self.code)
    