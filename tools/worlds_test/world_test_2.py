from functools import reduce
import operator
from more_itertools import set_partitions
import time
from math import comb as C

# https://stackoverflow.com/questions/19368375/set-partitions-in-python/30134039#30134039

# very slow, obviously overgenerates ridiculously

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


L = 'abcdefghijklmnopqrstuvwxyz'
L = L[:20]

target = len(L) // 3

def check(p):
    if abs(len(p[0]) - len(p[1])) > 1:
        return False
    
    if abs(len(p[1]) - len(p[2])) > 1:
        return False
        
    return abs(len(p[0]) - len(p[2])) < 2

total = n_assignments(len(L))

start = time.perf_counter()
i = 0
for partition in filter(check, set_partitions(L, 3)):
    i += 1

    if (not i % 1000):
        if time.perf_counter() - start >= 1:
            print(f'{time.perf_counter() - start:,.2f} seconds: {i:,} ({i / total * 100:.2f})% ...')
    
print(f'{time.perf_counter() - start:,.2f} seconds: {i:,} ({i / total * 100:.2f})%')
print()
