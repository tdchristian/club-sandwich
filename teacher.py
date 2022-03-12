from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from club import Club

class Teacher:
    """
    Represents a teacher. Has a name, day use trackers, and clubs.

    A teacher's prechosen days are the ones they're available to take clubs on.
    Their free days are (at any given moment) the ones without a club yet.
    Their taken days are (at any given moment) the ones with a club already.
    Their clubs are (at any given moment) the list of clubs they teach.

    TODO There is currently no data source to account for different pre days.
    """
    __slots__ = ('name', 'pre_days', 'free_days', 'taken_days', 'clubs')

    name: str
    pre_days: set[int]
    free_days: set[int]
    taken_days: set[int]
    clubs: set[Club]

    def __init__(self: Teacher, name: str) -> None:
        """
        Initialize a teacher with the given name.
        Prechosen days are currently hardcoded.
        Free days are equal to the prechosen ones and taken days start empty.
        Clubs start empty.
        """
        self.name = name
        self.pre_days = {0, 1, 2}
        self.free_days = self.pre_days.copy()
        self.taken_days = set()
        self.clubs = set()

    def take_day(self: Teacher, day: int) -> None:
        """
        Take the given day, if it's among the teacher's prechosen days.
        """
        if day in self.pre_days:
            self.taken_days.add(day)
            self.free_days.remove(day)

    def take_days(self: Teacher, days: set[int]) -> None:
        """
        Take each of the given days,
        if they're among the teacher's prechosen days.
        """
        for day in days:
            self.take_day(day)

    def is_day_free(self: Teacher, day: int) -> bool:
        """
        Return True iff the given day is free for this teacher.
        """
        return day in self.free_days

    def reset_day(self: Teacher, day: int) -> None:
        """
        Reset the given day's status, i.e. make it free and not taken,
        if it's among the teacher's prechosen days.
        """
        if day in self.pre_days:
            self.free_days.add(day)
            self.taken_days.remove(day)

    def reset_days(self: Teacher) -> None:
        """
        Reset the given days' status, i.e. make them free and not taken,
        if they're among the teacher's prechosen days.
        """
        for day in range(3):
            self.reset_day(day)

    def add_club(self: Teacher, club: Club) -> None:
        """
        Add the given club to the teacher's roster.
        """
        self.clubs.add(club)

    def remove_club(self: Teacher, club: Club) -> None:
        """
        Remove the given club from the teacher's roster, if it's on it.
        """
        if club in self.clubs:
            self.clubs.remove(club)
    
    def reset_clubs(self: Teacher) -> None:
        """
        Reset the teacher's roster of clubs to empty.
        """
        self.clubs = set()

    def __repr__(self: Teacher) -> str:
        """
        Return a string representation of this teacher (its name).
        """
        return self.name
