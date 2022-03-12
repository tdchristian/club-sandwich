from __future__ import annotations
from club import Club
from club_instance import ClubInstance

class Student:
    """
    Represents an individual student.
    Has a name, a grade, and a gender.
    Has preselected clubs, choices (keyed by priority), and unavailable days.

    After distribution, has a dictionary of choies gotten and of days to clubs.

    Tracks which choice is next for the purposes of distribution.
    Scores choices gotten for the purpose of ordering during distribution.

    Also has a reactivity representing the degree to which the student's
    chosen clubs are overfull.
    """
    __slots__ = ('name', 'grade', 'gender', 'choices', 'pres', 'days_unavailable', 'choices_gotten', 'days', 'next_choice_key', 'first_choice_key', 'choices_gotten_score', 'choices_gotten_weights', 'reactivity')

    name: str
    grade: int
    gender: str

    choices: dict[int, str]
    pres: dict[str, int]
    days_unavailable: set[int]

    choices_gotten: dict[int|str, int]
    days: dict[int, str]

    next_choice_key: int
    first_choice_key: int

    choices_gotten_score: int
    choices_gotten_weights: tuple[int]

    reactivity: int
    
    def __init__(self: Student, name: str, grade: int, gender: str,
                 choices: list[str], days_unavailable: set[int]=set()) -> None:
        """
        Initialize this student with the given data. The indices in choices
        are reinterpreted as keys so as to preserve identity under deletion
        (and are 1-indexed rather than 0-indexed from now on).

        Reset the distribution values for a blank slate.
        """
        
        self.name = name
        self.grade = grade
        self.gender = gender
        self.pres = {}
        
        self.days_unavailable = days_unavailable
        self.reactivity = 0

        self.choices = {}
        for (i, choice) in enumerate(choices):
            self.choices[i + 1] = choice
        
        self.first_choice_key = min(self.choices) if self.choices else 0

        self.choices_gotten_weights = (12, 8, 5, 2, 1)
        self.reset_distribution()

    def remaining_choice_indices(self: Student) -> list[int]:
        """
        Return a list of the choice keys not yet tried for distribution.
        """
        return list(i for i in range(self.next_choice_key, 6) if i in self.choices)

    def get_next_choice(self: Student) -> str|None:
        """
        Return the student's next untried choice (as a club code),
        or None if all possible choices have been tried.
        """

        # Already in one club per day
        if len(self.days) == 3:
            return None

        # All choices have been tried
        remaining_choice_indices = self.remaining_choice_indices()
        if not remaining_choice_indices:
            return None

        # Get the next choice and increment the next choice key
        choice = self.choices[remaining_choice_indices[0]]
        self.next_choice_key = remaining_choice_indices[0] + 1
        return choice

    def unregister_choice(self: Student, club_code: str) -> None:
        """
        Unregister the given club code from this student's choices.
        Update the first choice key based on what's left.
        """
        for (key, other) in self.choices.copy().items():
            if other == club_code:
                del self.choices[key]
        
        self.first_choice_key = min(self.choices) if self.choices else 0

    def register_pre_choice(self: Student, club: Club, n_times: int) -> None:  
        """
        Register the given club as a preselected one for this student,
        including the number of instances. If the club was among our choices,
        unregister it therefrom to avoid being placed in it again.
        """
        self.pres[club.code] = n_times
        self.unregister_choice(club.code)

    def add_to_club(self: Student, instance: ClubInstance) -> None:
        """
        Add this student to the given club instance. Update the record
        of choices gotten. The club could have been preselected, one
        we chose, or one we were placed into as a last resort (unchosen).
        """
        code = instance.club.code
        n_days = instance.club.days_per_instance

        # Place the club code on each day in the instance
        # TODO Could place the instance key here too
        for day in instance.days:
            self.days[day] = code

        # Note which choice was gotten

        # Preselected
        if code in self.pres:
            self.choices_gotten['pre'] += n_days
        
        else:

            # One of our choices
            for (key, other) in self.choices.items():

                # Checking 0 in the event that a choice was allowed to repeat
                if other == code and self.choices_gotten[key] == 0:
                    self.choices_gotten[key] += n_days
                    self.choices_gotten_score += self.choices_gotten_weights[key - 1]
                    break

            # Not one of our choices
            else:
                self.choices_gotten['unchosen'] += n_days

        # Eliminate remaining choice gotten records once we've got enough choices
        # e.g., if it took us 3 choices to get 3 days full, don't consider choices 4, 5
        if len(self.days) == 3:
            for key in self.remaining_choice_indices():
                del self.choices_gotten[key]

    def free_days(self: Student) -> set[int]:
        """
        Return the set of days this student still has free and available.
        """
        return {0, 1, 2}.difference(self.days_unavailable).difference(set(self.days))

    def reset_distribution(self: Student) -> None:
        """
        Reset the distribution status of this student:
        1. No days/clubs
        2. No choices gotten or choices gotten score
        3. Next choice key reset
        """
        self.days = {}
        self.next_choice_key = self.first_choice_key

        self.choices_gotten = {}

        for key in self.choices:
            self.choices_gotten[key] = 0
            
        self.choices_gotten['pre'] = 0
        self.choices_gotten['unchosen'] = 0
        self.choices_gotten_score = 0

    def __repr__(self: Student) -> str:
        """
        Return a string representation of this student (name, grade, gender).
        """
        return f'{self.name:<24} ({self.grade:<2} {self.gender})'
