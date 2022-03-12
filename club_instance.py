from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from club import Club
    from student import Student

class ClubInstance:
    """
    An individual instance of a club; that is, one group of students in it.
    An instance can have multiple days, corresponding to the host club's
    days per instance value. For example, choir may have 1 group of students
    who all meet on 3 days; that's 1 instance. Or ping pong may have 3
    different groups of students that each meet 1 day; that's 3 instances.

    Clubs that are allowed to grow will auto-expand by adding instances to
    accommodate a student who can't fit. Expanded instances are marked as such
    so that they can be purged without affecting the main distribution.

    Instance keys are not permanent. They are re-keyed if others are deleted.
    """
    __slots__ = ('key', 'club', 'days', 'students', 'expanded')

    club: Club
    key: str
    days: set[int]
    students: set[Student]
    expanded: bool
    
    def __init__(self: ClubInstance, club: Club, key: str, days: set[int], expanded: bool=False) -> None:
        """Set the club's core values. No special processing is done."""
        self.club = club
        self.key = key
        self.days = days
        self.students = set()
        self.expanded = expanded
    
    def can_add_student(self: ClubInstance, student: Student) -> bool:
        """
        Return True iff this instance can add the given student.
        This is so if the instance is not full and the student has enough free
        days for this instance to occupy.
        """
        return (not self.is_full()) and self.has_enough_days(student)

    def add_student(self: ClubInstance, student: Student) -> None:
        """
        Add the given student to this club instance, and vice versa.
        Does NOT check can_add_student first, in order to provide a force.
        If you want to check it, do so independently in the caller.

        TODO This behaviour may be changed later using an optional flag.
        """
        self.students.add(student)
        student.add_to_club(self)

    def reset_students(self: ClubInstance) -> None:
        """
        Purge the students in this instance.
        Does not remove data on the student's side.

        TODO This behaviour may be changed (inconsistent with add_student).
        """
        self.students = set()

    def is_full(self: ClubInstance) -> bool:
        """Return True if this instance is full."""
        return len(self.students) >= self.club.upper

    def has_enough_days(self: ClubInstance, student: Student) -> bool:
        """
        Return True iff the given student has enough free days
        to be added to this instance.
        """
        return len(self.days.intersection(student.free_days())) >= self.club.days_per_instance

    def repulsion(self: ClubInstance, student: Student) -> int:
        """
        Return the repulsion of the given student to this instance.
        The repulsion of a student to an instance is a measure of how many
        choices would become impossible were the student to join this instance.

        Specifically, for each day in this instance, tally how many days are
        shared with other clubs that the student hopes to take, weighted by
        whether that club is the student's 1st, 2nd, 3rd, 4th, or 4th choice.
        """
        days_to_repulsion = {}

        # Get all clubs the student is still trying to get into
        for key in student.remaining_choice_indices():            
            club_code = student.choices[key]
            club = self.club.school.clubs[club_code] # lol :')

            # For any days that would be free for the student, tally conflicts
            for day in club.taken_days().intersection(student.free_days()):
                days_to_repulsion[day] = days_to_repulsion.get(day, 0) + (6 - key)

        # Our repulsion score is the sum of tallies for days that we also share
        repulsion = 0
        for day in self.days:
            repulsion += days_to_repulsion.get(day, 0)
        
        return repulsion

    def mixedness(self: ClubInstance, expected: dict[object, float]) -> tuple[float]:
        """
        Return the mixedness values for this instance: (grade, gender)
        Each is a decimal between 0.0 and 1.0 representing the difference
        between the expected proportions and this instance's. Hence, greater
        values represent a proportion less aligned with the expected ones.

        For example, if the expected values are 0.50 (50%) male/female,
        and this instance is 0.75 male and 0.25 female, the difference
        in expected gender proportions is 0.25.
        """

        # If this instance is empty, don't count it
        n = len(self.students)
        if not n:
            return 0, 0

        # Make equivalent keys to the expected ones
        proportions = {}
        for key in expected:
            proportions[key] = 0

        # Tally students of each type
        for student in self.students:
            proportions[student.grade] += 1
            proportions[student.gender] += 1

        # Turn it into a proportion
        for (k, v) in proportions.items():
            proportions[k] = v / n

        # Sum differences for each grade and gender
        mixed_grade = 0
        mixed_gender = 0

        for k in range(9, 14):
            mixed_grade += abs(expected[k] - proportions[k])

        for k in ('M', 'F', 'O'):
            mixed_gender += abs(expected[k] - proportions[k])

        # Divide by how many grades or genders were examined
        return mixed_grade / 5, mixed_gender / 3

    def __repr__(self: ClubInstance) -> str:
        """Return the string representation of this instance."""
        return f'{self.club.code} {self.key} ({len(self.students)})'
