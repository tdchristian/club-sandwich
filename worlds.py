from typing import Iterator
import random
import itertools

from club import Club
from school import School

# Factor to divide repulsion by for "fuzziness"
REPULSION_SMOOTHING = 1

# Helper functions

def _filter_split_days(school: School, club: Club, days: set[int], club_to_days_used: dict[str, list[int]]) -> set[int]:
    """
    Return the given set of days, minus any days taken by other branches,
    if the club is split and this branch requires separate days.
    """
    if club.code not in school.splits_to_separate_days:
        return days

    # Get all branches and remove any days they have used
    # TODO As in School, don't track force_separate_days for the peer clubs 
    for (other_code, force_separate_days) in school.splits_to_separate_days[club.code].items():
        peer_codes = set(school.get_all_split_codes(other_code)).difference({club.code})
        for peer_code in peer_codes:
            for i in range(3):
                if i in days and club_to_days_used[peer_code][i] > 0:
                    days.remove(i)

    return days

def _day_is_available(club: Club, day: int, club_to_days_used: dict[str, list[int]], teacher_to_days_used: dict[str, list[bool]]) -> bool:
    """
    Return True iff the given day is available for the given club.
    A day is available if it's in the club's prechosen days,
    is not already used for more than maximum number of instances,
    and is free for the club's teacher (if it has one).
    """
    return all((
        (day in club.pre_days),
        (club_to_days_used[club.code][day] < club.max_instances_per_day),
        (club.teacher is None) or (not teacher_to_days_used[club.teacher.name][day])
    ))

def _available_days(school: School, club: Club, club_to_days_used: dict[str, list[int]], teacher_to_days_used: dict[str, list[bool]]) -> set[int]:
    """
    Return the available days for the given club.
    """
    base = set(filter(lambda day: _day_is_available(club, day, club_to_days_used, teacher_to_days_used), {0, 1, 2}))
    return _filter_split_days(school, club, base, club_to_days_used)

def _tally_block_repulsion_to_club(block: list[Club], club: Club) -> int:
    """
    Return the total repulsion factor the given block offers
    to the given club.
    """
    return sum(other.repulsion(club) for other in block)

def _tally_block_mutual_repulsion(block: list[Club]) -> int:
    """
    Return the total mutual repulsion factor for all the clubs
    in the given block.
    """
    return sum(_tally_block_repulsion_to_club(block, c) for c in block)

def _tally_block_mutual_repulsions(blocks: list[Club]) -> list[int]:
    """
    Return a list of day-indexed integers representing the total mutual
    mutual repulsion factor for all the clubs on that day.

    Can be used for debugging to check repulsion balance across days.
    """
    return list(_tally_block_mutual_repulsion(b) for b in blocks)

def _tally_repulsions(club: Club, blocks: list[Club], days: set[int]) -> dict[int, int]:
    """
    Return a dictionary mapping days to their repulsion to the given club.
    """
    return {i: _tally_block_repulsion_to_club(blocks[i], club) for i in days}

def _copy_blocks(blocks: list[list[Club]]) -> list[list[Club]]:
    """
    Return a deep copy of the given list of blocks.
    """
    return [blocks[0][:], blocks[1][:], blocks[2][:]]

def _copy_instances(orig: dict[str, list[set[int]]]) -> dict[str, list[set[int]]]:
    """
    Return a deep copy of the given dictionary mapping club codes
    to a list of instance day sets.
    """
    new = {}
    for (key, instances) in orig.items():
        new[key] = []
        for days in instances:
            new[key].append(days.copy())
    return new

def _copy_days_used(orig: dict[str, list[int]]) -> dict[str, list[int]]:
    """
    Return a deep copy of the given dictionary mapping club codes
    to a 0-indexed list of counts of instances per day for that club.
    """
    new = {}
    for (key, inner) in orig.items():
        new[key] = inner[:]
    return new

def _get_sets_of_days(days: list[int], n: int) -> Iterator[set[int]]:
    """
    Yield all sets of size n from days (which is of size 3).
    """
    
    if n == 3:
        yield set(days)

    elif n == 2:
        for pair in itertools.pairwise(days):
            yield set(pair)

    elif n == 1:
        for day in days:
            yield {day}

# The real deal

def generate_worlds(school: School, clubs: list[Club], n_to_yield: int) -> Iterator[int]:
    """
    Distribute up to n_to_yield worlds after distributing the given clubs.
    A world is a distribution of clubs (specifically, club instances) to days.

    N.B. The actual data yielded is only the number of worlds created so far.
    The clubs are changed in-place by creating the distributed instances,
    and MUST be reset before the iterator is advanced to function properly.

    Hence, a "phantom" representation is kept of the instances to be created
    at the end of each path. When yielding, these instances are created
    on the fly, but the phantom copy remains until all base cases are reached.
    """
    clubs_ = clubs[:]

    def _place_foreknown_instances(c: Club) -> bool:
        """
        Place the given club's foreknown instances, if any. This can arise
        if a club's required number of instances, days per instance, and
        available days mean that the instances can only be distributed one way.

        Return True if the club was foreknown and its instances were placed,
        and False if it was not foreknown. It is assumed that there are enough
        days to place the instances if they are foreknown.
        """
        if not c.instances_are_foreknown():
            return False
        
        # For each instance, determine the best day and create an instance
        for _ in range(c.min_instances):
            available_days = _available_days(school, c, club_to_days_used, teacher_to_days_used)
            if not available_days:
                print(c, c.code, 'bad')

            actual_days = set()
            for __ in range(c.days_per_instance):

                # Choose the one with the least days used so far
                i = min(available_days, key=lambda i: club_to_days_used[c.code][i])
                actual_days.add(i)
                available_days.remove(i)
            
            _create_phantom_instance(c, actual_days, club_to_instances, club_to_days_used, teacher_to_days_used)
        return True

    def _get_best_days(club: Club, blocks: list[list[Club]], club_to_days_used: dict[str, list[int]], teacher_to_days_used: dict[str, list[bool]]) -> list[int]:
        """
        Return the day or days that have the least repulsion for the given club
        considering the given blocks of clubs distributed so far.
        """
    
        # If all 3 days are needed, short-circuit
        if club.days_per_instance == 3:
            return [0, 1, 2]

        # Get available days, tally repulsions, sort by repulsions
        available = _available_days(school, club, club_to_days_used, teacher_to_days_used)
        repulsions = _tally_repulsions(club, blocks, available)
        order = sorted(repulsions, key=repulsions.get)
        
        # If 2 days are needed, take the first 2
        if (club.days_per_instance == 2):
            viable = order[:2]

            # If 2+3 would make as good a pair as 1+2, add that option
            if (len(order) > 2):
                sum_first_two = (repulsions[order[0]] + repulsions[order[1]]) // REPULSION_SMOOTHING
                sum_last_two = (repulsions[order[1]] + repulsions[order[2]]) // REPULSION_SMOOTHING
                if sum_first_two == sum_last_two:
                    viable.append(order[2])
        
        # If only 1 day is needed, add all options that are at the minimum
        else:
            viable = list(filter(lambda i: (repulsions[i] // REPULSION_SMOOTHING) == (repulsions[order[0]] // REPULSION_SMOOTHING), order))

        # Shuffle viable options, then sort by which have the fewest instances
        random.shuffle(viable)
        viable.sort(key=lambda i: c.days_used_counts.get(i, 0))

        return viable

    def _create_phantom_instance(club: Club, days: set[int], club_to_instances: dict[str, list[set[int]]], club_to_days_used: dict[str, list[int]], teacher_to_days_used: dict[str, list[bool]]) -> None:
        """
        Create a phantom instance for the given club on the given days.
        Tally it in the dictionary of clubs to instances, tally its days
        in the dictionary of clubs to days used, and if it has a teacher,
        mark the day used. Add it to the list of blocks for repulsion tallying.
        """
        club_to_instances[club.code].append(days)
        for day in days:
            blocks[day].append(club)

            club_to_days_used[club.code][day] += 1
            if club.teacher is not None:
                teacher_to_days_used[club.teacher.name][day] = True

    def _create_real_instances(club_to_instances: dict[str, list[set[int]]]) -> None:
        """
        For each club in the given dict, create a new instance from each
        of its sets of days. This amounts to distributing it to those days.
        """
        for club_ in clubs_:
            for days_ in club_to_instances[club_.code]:
                club_.create_instance(days_)

    def _take_path(clubs: list[Club], blocks: list[list[Club]], club_to_instances: dict[str, list[set[int]]], club_to_days_used: dict[str, list[int]], teacher_to_days_used: dict[str, list[bool]]) -> Iterator[None]:
        """
        Recursively distribute each of the given clubs to days. This means
        identifying the best (least repulsive) days, dividing them into sets
        of a size equal to what the club needs for an instance, and creating
        a phantom instance using those days. Once all clubs have their phantom
        instances, create the real instances and yield the option.
        """

        # Are there still clubs to distribute?
        if clubs:
            club = clubs[0]

            # Get the best (least repulsive) days and break them into sets
            best_days = _get_best_days(club, blocks, club_to_days_used, teacher_to_days_used)

            # For each equivalent distribution in terms of repulsion...
            for days in _get_sets_of_days(best_days, club.days_per_instance):

                # Make copies for the next branch of the path
                new_club_to_instances = _copy_instances(club_to_instances)
                new_club_to_days_used = _copy_days_used(club_to_days_used)
                new_teacher_to_days_used = _copy_days_used(teacher_to_days_used)

                # Create a phantom instance using those days
                _create_phantom_instance(club, days, new_club_to_instances, new_club_to_days_used, new_teacher_to_days_used)
                
                # Continue for the remaining days
                for path in _take_path(clubs[1:], _copy_blocks(blocks), new_club_to_instances, new_club_to_days_used, new_teacher_to_days_used):
                    yield path
        
        # No, they have all been distributed; end of the path
        else:
            _create_real_instances(club_to_instances)
            # print(_tally_block_mutual_repulsions(blocks)) # Debugging
            yield None

    # Prepare the records of phantom instances

    club_to_instances = {c.code: [] for c in clubs}
    club_to_days_used = {c.code: [0, 0, 0] for c in clubs}
    teacher_to_days_used = {c.teacher.name: [False, False, False] for c in clubs if c.teacher is not None}

    # Prepare the lists used to track repulsions and progress

    blocks = [[], [], []]
    clubs_free = []

    # Distinguish foreknown instances from distributable clubs

    for c in clubs:
        result = _place_foreknown_instances(c)

        # If not foreknown, add the club as many times as its minimum instances
        if result is False:
            n = c.min_instances
            for _ in range(n):
                clubs_free.append(c)

    # Sort the free clubs by total repulsion factor (descending)

    clubs_free.sort(key=lambda c: -c.repulsions['_total'])

    # Take all the possible paths and yield the number yielded so far

    n = 0
    for _ in _take_path(clubs_free, _copy_blocks(blocks), _copy_instances(club_to_instances), _copy_days_used(club_to_days_used), _copy_days_used(teacher_to_days_used)):
        if n < n_to_yield:
            n += 1
            yield n
        else:
            return
