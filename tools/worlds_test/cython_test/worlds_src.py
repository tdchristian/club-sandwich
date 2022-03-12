from itertools import combinations
from functools import reduce
from math import comb as C
from typing import Iterator, Tuple
import operator

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
        C(n_clubs - n_block_1 - n_block_2, n_block_3)
    ]

    return reduce(operator.mul, multiplicands, 1) // divisor

def assignments_yield(n_clubs: int) -> Iterator[set]:

    n_block_1 = n_clubs // 3 + ((n_clubs % 3) > 0)
    n_block_2 = n_clubs // 3 + ((n_clubs % 3) > 1)

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

    def _continue(i: int) -> int:

        if i < run[0]:
            return 0
        elif i <= run[1]:
            return 1 # illegal too slow for now
        else:
            try:
                next_run = next(runner)
                run[0], run[1] = next_run
                return _continue(i)
            except:
                return -1
                
    run = [0, 0]
    i = 1

    runner = _get_runs()
    
    choices = set(range(n_clubs))

    for block_1 in combinations(choices, n_block_1):
        _c = _continue(i)
        if _c == -1:
            return
        elif _c == 0:
            i += 1
            continue

        rest_2 = choices.difference(block_1)
        for block_2 in combinations(rest_2, n_block_2):
            _c = _continue(i)
            if _c == -1:
                return
            elif _c == 0:
                i += 1
                continue

            block_3 = rest_2.difference(block_2)
            _c = _continue(i)
            if _c == -1:
                return
            elif _c == 0:
                i += 1
                continue

            i += 1
            yield (block_1, block_2, block_3)

def generate_worlds(n_clubs: int, n_to_yield: int) -> Iterator[Tuple]:
    total = n_assignments(n_clubs)
    sets = assignments_yield(int(n_clubs))

    yielded = 0
    while (yielded < n_to_yield) and (yielded < total):
        yield next(sets)
        yielded += 1

for world in generate_worlds(30, 3):
    print(world)
