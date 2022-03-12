from __future__ import annotations
from re import L
from club import Club
from school import School
from student import Student

class Report:
    """
    Stores the key information from a world after distribution, derives
    statistics from said distribution, and calculates a numerical score.

    Three dictionaries storing data:

    students: {
        name: {
            'choices': list[int],
            'clubs': list[str],
            'max_clubs': in
        }
    }
    clubs: {
        code: {
            instance_key: {
                'days': set[int],
                'students': set[str],
                'mx grade': float,
                'mx gender': float
            }
        }
    }
    teachers: {
        name: {
            'days': {
                int: str
            },
            'nice names': list[str],
            'instance keys': list[str]
        }
    }

    One dictionary {str: float} storing derived statistics.

    1% 2% 3% 4% 5%: Tracks the % of students who received their Nth choice,
    if it was tried. Hence, the denominator is the students who had the choice
    available. For example, if they were in Choir, taking 3/3 days, they would
    not figure into any of these. But if they had 5 picks each taking 1 day,
    and got their 1st, 3rd, and 5th, they would increment the denominator for
    each of 1 through 5 and the numerator for 1, 3, 5.

    pre%: The % of students who received a club they were preselected for.
    If this is not 100% it signals conflicts in the preselections.
    TODO A club that was overridden by a later force would not be caught here.

    -1% -2% -3%: Tracks the % of students who had to be in N unchosen clubs.
    If a student ends up with a free day, they are currently placed in a random
    Study Hall and that gets tallied here.

    total%: Simply a sanity check; should equal 100% (all students have a club
    for all their available days).

    upper: The average number of students, across all instances,
    for the upper 10% of clubs.

    lower: The average number of students, across all instances,
    for the lower 10% of clubs.

    range: The difference between upper and lower.

    mx grade: The average variance across all clubs and instances compared to
    the expected proportions for grade mixing. See ClubInstance.mixedness.

    mx gender: The average variance across all clubs and instances compared to
    the expected proportions for gender mixing. See ClubInstance.mixedness.

    The class keeps flags for whether it has calculated the stats and score
    to avoid recalculation by mistake (TODO redundant).
    """

    __slots__ = ['stats', 'score', 'clubs', 'students', 'teachers', '_calculated_stats', '_calculated_score', 'full_names']

    stats: dict[str, float|int]
    score: int

    _calculate_stats: bool
    _calculate_score: bool

    clubs: dict[str, dict[str, object]]
    students: dict[str, dict[str, object]]
    teachers: dict[str, dict[str, object]]

    full_names: dict[str, str]
    
    def __init__(self: Report, clubs: list[Club], students: list[Student]) -> None:
        """
        Initialize the data for this report, including the stats dictionary.
        The club and student lists are used to preset the keys, but not stored.
        """

        self.stats = {}
        self.score = 0

        self._calculated_stats = False
        self._calculated_score = False
    
        self.clubs = {}
        self.students = {}
        self.teachers = {}

        for c in clubs:
            self.clubs[c.code] = {}

        for s in students:
            self.students[s.name] = {}

        # Python (3.10) does not allow it to be both slots and initialized
        self.full_names = {
            '1'             : '# of students who got their 1st choice if it was needed',
            '1%'            : '% who got their 1st choice if it was needed',
            '2'             : '# of students who got their 2nd choice if it was needed',
            '2%'            : '% who got their 2nd choice if it was needed',
            '3'             : '# of students who got their 3rd choice if it was needed',
            '3%'            : '% who got their 3rd choice if it was needed',
            '4'             : '# of students who got their 4th choice if it was needed',
            '4%'            : '% who got their 4th choice if it was needed',
            '5'             : '# of students who got their 5th choice if it was needed',
            '5%'            : '% who got their 5th choice if it was needed',
            'pre'           : '# of preselections that were successful',
            'pre%'          : '% of preselections that were successful',
            '-1'            : '# of students with 1 unasked-for Study Hall',
            '-1%'           : '% of student with 1 unasked-for Study Hall',
            '-2'            : '# of students with 2 unasked-for Study Halls',
            '-2%'           : '% of student with 2 unasked-for Study Halls',
            '-3'            : '# of students with 3 unasked-for Study Halls',
            '-3%'           : '% of student with 3 unasked-for Study Halls',
            'total'         : '# of student club assignments accounted for',
            'total%'        : '% of student club assignments accounted for',
            'upper'         : 'Average members in top 10% of clubs',
            'lower'         : 'Average members in bottom 10% of clubs',
            'range'         : 'Range between upper and lower averages',
            'mx grade'      : 'Variance from perfectly balanced grades',
            'mx gender'     : 'Variance from perfectly balanced genders',
    }

    def populate_world_distribution(self: Report, school: School, clubs: list[Club], students: list[Student]) -> None:
        """
        Given a school, clubs, and students in their state after distribution,
        extract the necessary information for this report to function.
        """
        
        # Populate student dictionary
        for s in students:
            self.students[s.name]['days'] = s.days.copy()
            self.students[s.name]['grade'] = s.grade
            self.students[s.name]['gender'] = s.gender
            self.students[s.name]['instance keys'] = ['', '', '']
            self.students[s.name]['nice names'] = ['', '', '']
            self.students[s.name]['choices'] = s.choices.copy()
            self.students[s.name]['choices gotten'] = s.choices_gotten.copy()

            # Add denominators for the choices that were possible to get
            denominators = {}
            for (key, _) in s.choices_gotten.items():
                if isinstance(key, int):
                    code = s.choices[key]
                    denominators[key] = school.clubs[code].days_per_instance
                elif key == 'pre':
                    denominators[key] = sum(((school.clubs[code].days_per_instance * s.pres[code]) for code in s.pres))
                
                denominators['total'] = 3 - len(s.days_unavailable)

            self.students[s.name]['choices gotten denominators'] = denominators

        # Populate the clubs dictionary
        for c in clubs:
            for i in c.instances.values():
                self.clubs[c.code][i.key] = {}
                nice_name = school.get_nice_name(c)
                
                self.clubs[c.code][i.key]['days'] = i.days.copy()
                self.clubs[c.code][i.key]['teacher'] = c.teacher if c.teacher is not None else ''
                self.clubs[c.code][i.key]['nice name'] = nice_name
                self.clubs[c.code][i.key]['students'] = set(s.name for s in i.students)

                # Extract additional data for students and teachers in the club
                for day in i.days:

                    # Student nice names, instance keys
                    for s in i.students:
                        self.students[s.name]['nice names'][day] = nice_name
                        self.students[s.name]['instance keys'][day] = i.key

                    # Teacher days, nice names, and instance keys
                    if c.teacher is not None:
                        teacher = c.teacher.name
                        if teacher not in self.teachers:
                            self.teachers[teacher] = {
                                'days': {},
                                'nice names': ['', '', ''],
                                'instance keys': ['', '', '']
                            }
                        
                        self.teachers[teacher]['days'][day] = c.code
                        self.teachers[teacher]['nice names'][day] = nice_name
                        self.teachers[teacher]['instance keys'][day] = i.key

                # Add grade & gender proportion reports
                mx_grade, mx_gender = i.mixedness(school.proportions)
                self.clubs[c.code][i.key]['mx grade'] = mx_grade
                self.clubs[c.code][i.key]['mx gender'] = mx_gender

    def calculate_stats(self: Report) -> dict[str, float|int]:
        """
        Calculate (if not yet done) the statistics and return the results.
        """
        if not self._calculated_stats:
            self._calculate_stats()
            self._calculated_stats = True
        return self.stats

    def _calculate_stats(self: Report) -> None:
        """
        Calculate the statistics and save them to self.stats.
        """
        n_students = len(self.students)
        n_clubs = len(self.clubs)
        self.stats = {k: 0.0 for k in self.full_names}

        # Students

        # The denominator for each of the % categories has to be tallied
        nth_choice_to_denominator = {
            '1': 0,
            '2': 0,
            '3': 0,
            '4': 0,
            '5': 0,

            # TODO Should these denominators really be the unfiltered ones?
            '-1': 3 * n_students,
            '-2': 3 * n_students,
            '-3': 3 * n_students,

            'pre': 0,
            'total': 0
        }

        # Tally each type of choice gotten
        for (name, data) in self.students.items():

            # Unchosen club is a # representing how many days were unchosen
            if 'unchosen' in data['choices gotten']:
                n = data['choices gotten']['unchosen']
                if n > 0:
                    self.stats[f'-{n}'] += 1

            # Others are # represents how many days are in that choice
            for (key, n) in data['choices gotten'].items():
                self.stats['total'] += n

                if key == 'unchosen':
                    continue

                self.stats[f'{key}'] += n
                nth_choice_to_denominator[f'{key}'] += data['choices gotten denominators'][key]
            
            # Add this student's total to the total denominator
            nth_choice_to_denominator['total'] += data['choices gotten denominators']['total']

        # Reduce these numbers to percentages

        for key in ['pre', 'total'] + list(i for i in range(-3, 0)) + list(i for i in range(1, 6)):
            n = self.stats[f'{key}']
            d = nth_choice_to_denominator[f'{key}']
            # print(f'{key:<8} {n:>3} / {d:>4}')
            self.stats[f'{key}%'] = n / d * 100
            del self.stats[f'{key}']

        # Clubs / instances

        # Count instances
        n_clubs = len(self.clubs)
        n_instances = 0
        for club_data in self.clubs.values():
            for i_data in club_data.values():
                n_instances += 1

        def _n_students_in_club(club_code: str) -> int:
            """
            Return the number of students across all instances
            of the given club code.
            """
            instance_keys = self.clubs[club_code].keys()
            return sum((len(self.clubs[club_code][i_key]['students']) for i_key in instance_keys))

        # Upper, lower, and range of students in clubs

        # Sort by number of students, ascending
        sorted_clubs = sorted(self.clubs.keys(), key=lambda c: _n_students_in_club(c))

        n_sample = n_clubs // 10

        lower = 0
        for c in sorted_clubs[:n_sample]:
            lower += _n_students_in_club(c)
        lower //= n_sample
        
        upper = 0
        for c in sorted_clubs[-n_sample:]:
            upper += _n_students_in_club(c)
        upper //= n_sample

        self.stats['lower'] = lower
        self.stats['upper'] = upper
        self.stats['range'] = upper - lower

        # Average the mixedness of grade and gender across all clubs
        total_mx_grade = 0
        total_mx_gender = 0
        for club_data in self.clubs.values():
            for i_data in club_data.values():
                mx_grade = i_data['mx grade']
                mx_gender = i_data['mx gender']
            total_mx_grade += mx_grade
            total_mx_gender += mx_gender
        
        self.stats['mx grade'] = total_mx_grade / n_clubs
        self.stats['mx gender'] = total_mx_gender / n_clubs

    def calculate_score(self: Report) -> int:
        """        
        Calculate (if not yet done) the statistics and return the results.
        """
        if not self._calculated_score:
            self._calculate_score()
            self._calculated_score = True
        return self.score

    def _calculate_score(self: Report) -> None:
        """
        Calculate the score and save it to self.score.

        TODO Weights should probably be constants.
        """
        self.calculate_stats()
        self.score = 0
        
        # The more students in clubs they chose, the better
        self.score += (12 * self.stats['1%'])
        self.score += (8 * self.stats['2%'])
        self.score += (5 * self.stats['3%'])
        self.score += (3 * self.stats['4%'])
        self.score += (2 * self.stats['5%'])

        # The more students in clubs they didn't choose, the worse
        self.score -= (3 * self.stats['-1%'])
        self.score -= (5 * self.stats['-2%'])
        self.score -= (20 * self.stats['-3%'])

        # The wider the range, the worse
        self.score -= ((0.05 * (self.stats['range']) ** 2))

        # The more the variance from expected proportions, the worse
        self.score -= (1000 * self.stats['mx grade'])
        self.score -= (1000 * self.stats['mx gender'])

        # No point in excessive precision
        self.score = int(self.score)

    def n_students(self: Report, club: Club) -> int:
        """
        Return the number of students that got into the given club.
        """
        if club.code not in self.clubs:
            return 0
        else:
            return sum(len(i['students']) for i in self.clubs[club.code].values())
        
    def format_report(self: Report) -> str:
        """
        Return a string of stats in this report formatted as key: value.
        Does not use the full names -- this is primarily for debugging.

        TODO Sorting relies on Python dict ordering...
        """

        def _format_piece(key: str, val: str) -> str:
            """Return the given key, value pair formatted as key: value."""
            piece = f'{key:<10}: {val:.1f}'.rstrip('0').rstrip('.')

            # Add a % for values that are meant to be percentages
            if key.endswith('%'):
                piece += '%'
            
            return piece

        pairs = [('score', self.score)] + [item for item in self.stats.items()]
        pieces = [_format_piece(*p) for p in pairs]
        return '\n'.join(pieces)

    def __repr__(self: Report) -> str:
        """Return a string representation of this report (its score)."""
        return f'{self.score}'
