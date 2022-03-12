import club_sandwich
from tools.prompts import p_choice

def main() -> None:
    """
    Ask the user for a program to execute and execute it.
    """
    programs = (
        ('Create schedule'                      , club_sandwich.create_schedule),
        ('Pre-process votes'                    , club_sandwich.process_votes_only),
        ('Print input specifications'           , club_sandwich.print_input_specs),
        ('Resave reports to refresh formatting' , club_sandwich.resave_all_reports),
    )

    while True:
        choices = list(t[0] for t in programs)

        print()
        choice = p_choice('Choose a program or blank to exit', choices, allow_blank=True)

        if not choice:
            return

        print()
        programs[choice - 1][1]()
        print('=' * 80)

if __name__ == '__main__':
    main()
