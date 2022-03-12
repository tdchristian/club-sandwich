from itertools import combinations, islice
from functools import reduce
from math import comb as C
import math
from typing import Generator, Iterator
from prompts import p_choice, p_int, p_bool
import operator
import os
import time

# Make a charset of A-Za-Z0-9
CHARSET = ''
for i in range(65, 91):
    CHARSET += chr(i)
for i in range(97, 123):
    CHARSET += chr(i)
for i in range(48, 58):
    CHARSET += chr(i)

# Test data
NO_COMBOS = (
    set('AB'),
    set('BE'),
    set('CS'),
    set('DL'),
    set('EH')
)

def n_assignments(n_clubs: int, naive: bool=False) -> int:
    n_block_1 = n_clubs // 3 + ((n_clubs % 3) > 0)
    n_block_2 = n_clubs // 3 + ((n_clubs % 3) > 1)
    n_block_3 = n_clubs // 3

    if naive:
        divisor = 1
    elif n_clubs % 3:
        divisor = 2
    else:
        divisor = 6
    
    multiplicands = [
        C(n_clubs, n_block_1),
        C(n_clubs - n_block_1, n_block_2),        
        C(n_clubs - n_block_1 - n_block_2, n_block_3),
        1 / divisor
    ]

    return int(reduce(operator.mul, multiplicands, 1))

def assignments_yield(n_clubs: int) -> Iterator[set]:

    n_block_1 = n_clubs // 3 + ((n_clubs % 3) > 0)
    n_block_2 = n_clubs // 3 + ((n_clubs % 3) > 1)
    # n_block_3 = n_clubs // 3

    def _get_runs() -> Iterator[tuple]:

        if (n_clubs % 3) < 2:
            r = (n_clubs // 3) - 1
            n = (2 * r) + 1
            step = C(n, r)
            limit = n_assignments(n_clubs, True)

            if not (n_clubs % 3):
                limit //= 3

            for i in range(0, limit, step * 2):
                yield (i + 1, i + step)

        else:
            # all good run
            i = n_assignments(n_clubs - 1, True)
            yield(1, i)
            i += 1

            p_r = n_clubs // 3
            p_n = 2 * p_r
            dupes = C(p_n, p_r)
            goods = C(p_n, p_r + 1)

            s_r = n_clubs // 3
            s_n = 3 * s_r
            sub_runs = C(s_n, s_r)

            for _ in range(n_clubs // 3):
                # print(f'Now to do {sub_runs} runs of {dupes} dupes to {goods} goods')

                # length x period
                for __ in range(sub_runs):
                    i += dupes + goods
                    yield(i - goods, i - 1)
                
                p_r -= 1
                p_n -= 1
                change = C(p_n, p_r)
                dupes += change
                goods -= change

                s_n -= 1
                sub_runs = C(s_n, s_r)

            # rest is all dupes

    def _remove_combo(super: str, sub: str) -> str:
        return ''.join(filter(lambda c: c not in sub, super))

    def _continue(i: int, block: str) -> int:
        # 0 = skip
        # 1 = do
        # -1 = stop all

        if i < run[0]:
            return 0
        elif i <= run[1]:
            return 1 # illegal too slow for now
            return int(block and not _illegal(block))
        else:
            try:
                next_run = next(runner)
                run[0], run[1] = next_run
                _continue(i, block)
            except:
                return -1

    def _illegal(block: set) -> bool:
        return any(co.issubset(block) for co in NO_COMBOS)
                
    run = [0, 0]
    i = 1

    runner = _get_runs()
    
    # choices = set(CHARSET[:n_clubs])
    choices = set(range(n_clubs))

    for block_1 in combinations(choices, n_block_1):
        _c = _continue(i, block_1)
        if _c == -1:
            return
        elif _c == 0:
            i += 1
            continue

        rest_2 = choices.difference(block_1)
        for block_2 in combinations(rest_2, n_block_2):
            _c = _continue(i, block_2)
            if _c == -1:
                return
            elif _c == 0:
                i += 1
                continue

            block_3 = rest_2.difference(block_2)
            _c = _continue(i, block_3)
            if _c == -1:
                return
            elif _c == 0:
                i += 1
                continue

            i += 1
            yield (block_1, block_2, block_3)
            # yield set((''.join(block_1), ''.join(block_2), ''.join(block_3)))

def program_n_assignments():
    n_clubs = p_int('Number of clubs, or blank to stop', allow_blank=True)
    while n_clubs:
        n = n_assignments(int(n_clubs))
        print(f'{n} possible assignments')
        
        n_clubs = p_int('\nNumber of clubs, or blank to stop', allow_blank=True)

def program_assignments_yield(n_clubs: int=0, silent: bool=True):    

    def _sub(n_clubs: int) -> None:
        sets = assignments_yield(int(n_clubs))
        n = n_assignments(int(n_clubs))
        print(f'{n_clubs} clubs : theoretical total {n:,} assignments')

        if p_bool(f'Loop through them'):
            total = 0
            start = time.time()
            for s in sets:

                if not silent:
                    print(' | '.join(str(b) for b in sorted(s, key=lambda b: -len(b))))

                total += 1
                if (not total % (10 ** (math.ceil(n_clubs / 3) - 1))):
                    if time.time() - start >= 1:
                        print(f'{time.time() - start:,.2f} seconds: {total:,} ({total / n * 100:.2f})% ...')
        
            print(f'\n{time.time() - start:,.2f} seconds: {total:,} ({total / n * 100:.2f}%)')

    if n_clubs != 0:
        _sub(n_clubs)

    else:
        n_clubs = p_int('Number of clubs, or blank to stop', allow_blank=True)
        while n_clubs:
            _sub(n_clubs)
            
            n_clubs = p_int('\nNumber of clubs, or blank to stop', allow_blank=True)

def assignments_yield_islice(n_clubs: int) -> Iterator[set]:
    # This is almost but not quite accurate
    # It's about 15% faster than non-islice, but I can't get the combinators to roll over right

    n_block_1 = n_clubs // 3 + ((n_clubs % 3) > 0)
    n_block_2 = n_clubs // 3 + ((n_clubs % 3) > 1)

    is_R2 = (n_clubs % 3) > 1

    n1 = n_assignments(n_clubs, True)
    c2 = C(n_clubs - n_block_1, n_block_2) - ((n_clubs % 3) > 1)

    def _get_runs() -> Iterator[tuple]:

        if (n_clubs % 3) < 2:
            r = (n_clubs // 3) - 1
            n = (2 * r) + 1
            step = C(n, r)
            limit = n_assignments(n_clubs, True)

            if not (n_clubs % 3):
                limit //= 3

            for i in range(0, limit, step * 2):
                yield [i + 1, i + step]

        else:
            # all good run
            i = n_assignments(n_clubs - 1, True)
            yield [1, i]
            i += 1

            p_r = n_clubs // 3
            p_n = 2 * p_r
            dupes = C(p_n, p_r)
            goods = C(p_n, p_r + 1)

            s_r = n_clubs // 3
            s_n = 3 * s_r
            sub_runs = C(s_n, s_r)

            for _ in range(n_clubs // 3):
                # print(f'Now to do {sub_runs} runs of {dupes} dupes to {goods} goods')

                # length x period
                for __ in range(sub_runs):
                    i += dupes + goods
                    yield [i - goods, i - 1]
                
                p_r -= 1
                p_n -= 1
                change = C(p_n, p_r)
                dupes += change
                goods -= change

                s_n -= 1
                sub_runs = C(s_n, s_r)

            # rest is all dupes

    def _advance(i: int, gen: Generator, tab: int=0) -> tuple:
        tab_ = '    ' * tab

        if i < run[0]:
            print(f'{tab_}skip from {i} to {run[0]}')
            skip = run[0] - i
            return True, skip, islice(gen, skip, None)

        elif i <= run[1]:
            return True, 0, gen

        else:
            try:
                run[0], run[1] = next(runs)
                print(f'{tab_}skip from {i} to {run[0]}')
                skip = run[0] - i
                return True, skip, islice(gen, skip, None)
            except:
                return False, None, None

    # choices = set(range(n_clubs))
    choices = set(CHARSET[:n_clubs]) # TODO temp
    runs = _get_runs()

    # First run
    run = next(runs)

    # Get blocks 1 generator
    combs_1 = combinations(choices, n_block_1)

    i = 1

    # Outer block until i is at n_assignments (naive version)
    while i <= n1:
        print(f'block 1 i: {i}')

        # Get next block 1
        block_1 = next(combs_1)
        print(f'c1 advanced: {block_1}')

        # Separate remainder
        rest_2 = choices.difference(block_1)

        # Get blocks 2 generator
        combs_2 = combinations(rest_2, n_block_2)

        go_on, skip, combs_2 = _advance(i, combs_2, 1)
        if not go_on:
            return
        i += skip

        # Inner block until at most all combinations of rest are tried
        n2 = i + c2
        while i < n2:
            print(f'    block 2 i: {i}')
            block_2 = next(combs_2)
            print(f'    c2 advanced: {block_2}')

            yield block_1, block_2, rest_2.difference(block_2)
            i += 1
            print(f'    i incremented to {i}')

            go_on, skip, combs_2 = _advance(i, combs_2, 1)
            if not go_on:
                return
            i += skip

        go_on, skip, combs_1 = _advance(i, combs_1)
        if not go_on:
            return
        i += skip

def program_verify_distinct(n_clubs: int=0, silent: bool=True):

    def _sub(n_clubs: int) -> None:
        sets = assignments_yield_islice(int(n_clubs))
        n = n_assignments(int(n_clubs))

        total = 0
        distinct = set()
        for s in sets:
            if not silent:
                nice = ''
                for b in s:
                    b = ''.join(sorted(b))
                    for c in b:
                        nice += str(c)
                    nice += ' '
                print('    ',nice,sep='    ')

            total += 1

            sig_pieces = []
            for b in s:
                sig_pieces.append(''.join(str(c) for c in sorted(b)))
            sig_pieces.sort(key=lambda b: (-len(b), b))
            sig = '|'.join(sig_pieces)
            distinct.add(sig)
        
        real_n = len(distinct)
        if real_n < n:
            op = '<'
        elif real_n == n:
            op = '='
        else:
            op = '>'
        
        print(f'{total:,} actual, of which {real_n:,} distinct {op} {n:,} theoretical ({real_n/n*100:,.2f}%)')

    if n_clubs != 0:
        _sub(n_clubs)

    else:
        n_clubs = p_int('Number of clubs, or blank to stop', allow_blank=True)
        while n_clubs:
            _sub(n_clubs)
            n_clubs = p_int('\nNumber of clubs, or blank to stop', allow_blank=True)


def set_cwd_to_file():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

def choose_program():
    programs = (
        ('Number of assignments'                                   , program_n_assignments),
        # ('Make assignments via set'                              , program_assignments_set),
        # ('Make assignments 2 (experimental)'                     , program_assignments_2),
        ('Make assignments via yield'                              , program_assignments_yield),
        ('Make assignments via yield+islice (not accurate for R2)' , program_assignments_yield),
        # ('Find duplicate period'                                 , program_dupes),
        # ('Find duplicate runs (r2)'                              , program_dupes_r2),
        # ('Save range of duplicate periods'                       , program_save_dupes),
        # ('Save range of assignments'                             , program_save),
        # ('Make assignments via custom combos'                    , program_assignments_custom),
        ('Verify distinctness counts for yield+islice'             , program_verify_distinct)
    )

    while True:
        choices = list(t[0] for t in programs)

        print()
        choice = p_choice('Choose a program or blank to exit', choices, allow_blank=True)

        if not choice:
            return

        print()
        programs[choice - 1][1]()

if __name__ == '__main__':
    set_cwd_to_file()
    choose_program()
