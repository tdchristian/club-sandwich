from functools import total_ordering
from multiprocessing.spawn import prepare
from school import School
import parse
import save
from world import World
import worlds
import time

N_WORLDS_TO_TEST = 1
N_STUDENT_CONFIGURATIONS_PER_WORLD = 100
N_BEST = 1

def prepare_school() -> School:
    """
    Ingest all the data and return a school object:
    merged clubs, split clubs, nice names,
    students, clubs, preselects, whitelists & blacklists, exclusions

    Calculate proportions and repulsions based on this data.
    Along the way, save raw and filtered versions of the votes.
    """
    school = School()

    # Needs to be done first to prepare for clubs later
    parse.parse_merges(school)
    parse.parse_splits(school)
    parse.parse_nice_names(school)

    parse.parse_students(school)
    parse.parse_clubs(school)
    parse.parse_preselects(school)
    parse.parse_whitelists(school)
    parse.parse_exclusions(school)

    school.calculate_proportions()

    # Tally votes to aid auto-filtering, and save raw data to help human decision-making
    school.tally_votes()
    save.save_summary_votes_csv(school, 'raw')
    save.save_all_club_votes_csvs(school, 'raw')

    school.remove_students_who_arent_eligible()
    school.remove_clubs_that_cannot_run()

    # Resave filtered data
    school.tally_votes()
    save.save_summary_votes_csv(school, 'filtered')
    save.save_all_club_votes_csvs(school, 'filtered')

    school.calculate_repulsions()
    # school.calculate_reactivities()

    return school

def get_best_worlds(school: School, validate_early: bool=False) -> list[tuple[int, World]]:
    """
    Run possible n_worlds * n_student_configurations distributions.
    Returns a list of (score, world) tuples trimmed to the n_best top scorers.

    With early validation, processing is greatly slowed, but invalid worlds are
    filtered out beforehand.
    """
    
    # Counters
    n_tested = 0
    n_valid = 0
    start = time.perf_counter()

    # Separate out these so we don't affect the original order
    best = []
    clubs = list(school.clubs.values())
    students = list(school.students.values())

    # Some things can be affected between creation and first distribution
    for s in students:
        s.reset_distribution()
    for c in clubs:
        c.reset_student_distribution()

    # Go through all worlds, in all student configurations
    for _ in worlds.generate_worlds(school, clubs, N_WORLDS_TO_TEST):
        for __ in range(N_STUDENT_CONFIGURATIONS_PER_WORLD):
    
            # Create and distribute! Student order is handled by the world
            world = World(school, clubs[:], students[:])
            world.distribute()

            # Validate early (intensive process)
            if validate_early:
                valid, msg = world.validate()
                n_valid += valid
            else:
                valid = True

            # Calculate score (intensive process)
            score = world.score()

            if valid:

                # Add it to the list of best in the proper place
                if len(best) < N_BEST:
                    best.append((score, world))
                elif score > best[0][0]:
                    best[0] = (score, world)

                best.sort(key=lambda t: t[0])

            # Reset student-only distributions
            for s in students:
                s.reset_distribution()
            for c in clubs:
                c.reset_student_distribution()

            # Progress counter
            n_tested += 1
            if not (n_tested % max(10, min(1_000, ((N_WORLDS_TO_TEST * N_STUDENT_CONFIGURATIONS_PER_WORLD) // 100)))):
                stem = f'{time.perf_counter() - start:,.2f} seconds: Tested {n_tested:,} worlds'
                if validate_early:
                    stem += f', {n_valid} valid'
                print(stem)
        
        # Reset instance/day distributions too
        for c in clubs:
            c.reset_entire_distribution()
        for s in students:
            s.reset_distribution()

    return best

def print_world_contents(world: World) -> None:
    """
    Print the contents of the given world (clubs -> instances -> days, n_students).
    """
    for (club, instances) in sorted(world.report.clubs.items(), key=lambda item: item[0].lower()):
        print(club)
        for (key, data) in instances.items():
            str_days = '/'.join((save.INT_TO_DAY_LETTER[d] for d in data['days']))
            print(' ' * 8 + f'{key:<2} : {len(data["days"])} days ({str_days}), {len(data["students"])} students')

def save_best_world_reports(best: list[tuple[int, World]]) -> None:
    """
    Save reports for the given list of (score, world) tuples.
    """
    for (i, (_, world)) in enumerate(best[::-1]):

        # Mostly debugging tbh
        # print(world.report.format_report())
        print()
        # save.save_summary_votes_csv(school, 'distributed', world.report)
        # print_world_contents(world)
        
        # Validate world
        valid, msg = world.validate()
        if valid:
            save.save_world_report(world.report, chr(65 + i))
        else:
            print(f'World was invalid! Report:\n{msg}')

def create_schedule() -> None:
    """
    Prepare the school, find the best worlds, and save their reports.
    """
    school = prepare_school()
    best_worlds = get_best_worlds(school, validate_early=False)
    save_best_world_reports(best_worlds)

def resave_all_reports() -> None:
    """
    Resave existing reports.
    """
    for key in 'ABC':
        save.resave_report(key)

def process_votes_only() -> None:
    """
    Prepare the school and save the votes data.
    """
    prepare_school()

def print_input_specs() -> None:
    """
    Pretty-print the contents of the input specifcations file.
    """
    files = parse.parse_input_specifications()
    for file in files.values():
        print(f'Filename: {file.filename}')
        print(f'Notes: {file.notes}')
        print(f'Source: {file.source}')
        print()
        print('Columns:')

        print(f'    {"Column":<26} | ', end='')
        print(f'    {"Datatype":<35} | ', end='')
        print(f'    {"Example":<22} | ', end='')
        print(f'    {"Default value":<23}')

        print("=" * 131)

        for column in file.columns:
            print(f'    {column.name:<26} | ', end='')
            print(f'    {column.datatype:<35} | ', end='')
            print(f'    {column.example:<22} | ', end='')
            print(f'    {column.default:<23}')
            if column.notes:
                print(f'    {column.notes}')
            print()

        print()
