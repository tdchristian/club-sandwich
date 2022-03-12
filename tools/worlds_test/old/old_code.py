
def program_assignments_combine():
    n_clubs = p_int('Number of clubs, or blank to stop', allow_blank=True)
    while n_clubs:
        sets = assignments_combine(int(n_clubs))
        print(f'{len(sets)} possible assignments')

        if p_bool('Show them'):
            print(format_sets_of_blocks(sets))
        
        n_clubs = p_int('\nNumber of clubs, or blank to stop', allow_blank=True)

def assignments_set(n_clubs: int) -> set:
    combos = set()
    choices = CHARSET[:n_clubs]

    n_block_1 = n_clubs // 3 + ((n_clubs % 3) > 0)
    n_block_2 = n_clubs // 3 + ((n_clubs % 3) > 1)
    n_block_3 = n_clubs // 3

    def _remove_combo(super: str, sub: str) -> str:
        return ''.join(filter(lambda c: c not in sub, super))

    for block_1 in combinations(choices, n_block_1):
        block_1 = ''.join(block_1)

        rest_2 = _remove_combo(choices, block_1)
        for block_2 in combinations(rest_2, n_block_2):
            block_2 = ''.join(block_2)

            rest_3 = _remove_combo(rest_2, block_2)
            for block_3 in combinations(rest_3, n_block_3):
                block_3 = ''.join(block_3)
                # print(f'{block_1} | {block_2} | {block_3}')

                combos.add(frozenset({block_1, block_2, block_3}))

    return combos

def assignments_combine(n_clubs: int) -> set:

    def _recurse(blocks: list, charset: str) -> None:
        if not charset:
            combos.add(frozenset(blocks))
            return

        for i in range(len(blocks)):
            blocks[i] += charset[0]
            _recurse(blocks[:], charset[1:])

    combos = set()
    charset = CHARSET[:n_clubs]
    _recurse(['', '', ''], charset)
    return combos

def assignments_3_combos(n_clubs: int) -> Iterator[set]:

    choices = CHARSET[:n_clubs]

    n_block_1 = n_clubs // 3 + ((n_clubs % 3) > 0)
    n_block_2 = n_clubs // 3 + ((n_clubs % 3) > 1)
    n_block_3 = n_clubs // 3

    divisible_by_3 = not bool(n_clubs % 3)
    if divisible_by_3:
        twos = dict()
    else:
        twos = set()

    def _remove_combo(super: str, sub: str) -> str:
        return ''.join(filter(lambda c: c not in sub, super))

    def _check_sig(block_a, block_b) -> bool:
        sig = sorted((block_a, block_b))
        sig = f'{sig[0]}|{sig[1]}'

        if len(twos) > 1000 and not len(twos) % 1000:
            print(f'twos: {len(twos):,}')

        if sig not in twos:
            if divisible_by_3:
                twos[sig] = 1
            else:
                twos.add(sig)

            return False

        else:
            if divisible_by_3:
                if twos[sig] == 5:
                    del twos[sig]
                else:
                    twos[sig] += 1
            else:
                twos.remove(sig)

            return True

    for block_1 in combinations(choices, n_block_1):
        block_1 = ''.join(block_1)

        rest_2 = _remove_combo(choices, block_1)
        for block_2 in combinations(rest_2, n_block_2):
            block_2 = ''.join(block_2)

            if _check_sig(block_1, block_2):
                continue

            rest_3 = _remove_combo(rest_2, block_2)
            for block_3 in combinations(rest_3, n_block_3):
                block_3 = ''.join(block_3)

                if _check_sig(block_1, block_3):
                    continue

                yield set((block_1, block_2, block_3))

def find_dupes(n_clubs: int) -> set:
    combos = set()
    choices = CHARSET[:n_clubs]

    n_block_1 = n_clubs // 3 + ((n_clubs % 3) > 0)
    n_block_2 = n_clubs // 3 + ((n_clubs % 3) > 1)
    n_block_3 = n_clubs // 3

    def _remove_combo(super: str, sub: str) -> str:
        return ''.join(filter(lambda c: c not in sub, super))

    i = 0
    dupes = []
    result = ''

    for block_1 in combinations(choices, n_block_1):
        block_1 = ''.join(block_1)

        rest_2 = _remove_combo(choices, block_1)
        for block_2 in combinations(rest_2, n_block_2):
            block_2 = ''.join(block_2)

            rest_3 = _remove_combo(rest_2, block_2)
            for block_3 in combinations(rest_3, n_block_3):
                block_3 = ''.join(block_3)

                dupe = frozenset({block_1, block_2, block_3}) in combos
                if dupe:
                    dupes.append(i + 1)
                result += f'{i + 1:<7}: {block_1} | {block_2} | {block_3} {"X" if dupe else ""}\n'

                combos.add(frozenset({block_1, block_2, block_3}))
                i += 1

    return dupes, result

def find_dupes_r2(n_clubs: int) -> set:
    combos = set()
    choices = CHARSET[:n_clubs]

    if (n_clubs % 3) != 2:
        return set()

    n_block_1 = n_clubs // 3 + ((n_clubs % 3) > 0)
    n_block_2 = n_clubs // 3 + ((n_clubs % 3) > 1)
    n_block_3 = n_clubs // 3

    def _remove_combo(super: str, sub: str) -> str:
        return ''.join(filter(lambda c: c not in sub, super))

    i = 0
    result = ''

    dupe_runs = []

    dupe_run = 0
    good_run = 0

    for block_1 in combinations(choices, n_block_1):
        block_1 = ''.join(block_1)

        rest_2 = _remove_combo(choices, block_1)
        for block_2 in combinations(rest_2, n_block_2):
            block_2 = ''.join(block_2)

            rest_3 = _remove_combo(rest_2, block_2)
            for block_3 in combinations(rest_3, n_block_3):
                block_3 = ''.join(block_3)

                dupe = frozenset({block_1, block_2, block_3}) in combos

                if dupe:
                    dupe_run += 1
                    if good_run:
                        dupe_runs.append(('good', good_run))
                    good_run = 0
                else:
                    good_run += 1
                    if dupe_run:
                        dupe_runs.append(('dupe', dupe_run))
                    dupe_run = 0

                result += f'{i + 1:<7}: {block_1} | {block_2} | {block_3} {"X" if dupe else ""}\n'

                combos.add(frozenset({block_1, block_2, block_3}))
                i += 1
    
    
    if dupe_run:
        dupe_runs.append(('dupe', dupe_run))
    
    if good_run:
        dupe_runs.append(('good', good_run))

    meta_dupe_runs = []
    meta_dupe_runs.append(dupe_runs[0][::-1])

    last_dupe = 0
    last_good = 0
    run_length = 0

    for i in range(1, len(dupe_runs) - 2, 2):
        _, dupe = dupe_runs[i]
        _, good = dupe_runs[i + 1]

        if dupe == last_dupe and good == last_good:
            run_length += 1
        else:
            if run_length > 0:
                meta_dupe_runs.append((f'{run_length} x dupe/good (total {(last_dupe + last_good) * run_length})', f'{last_dupe}/{last_good}'))
            last_good = good
            last_dupe = dupe
            run_length = 1
    
    
    if run_length > 0:
        meta_dupe_runs.append((f'{run_length} x dupe/good (total {(last_dupe + last_good) * run_length})', f'{last_dupe}/{last_good}'))

    
    meta_dupe_runs.append(dupe_runs[-1][::-1])
    return meta_dupe_runs

def program_dupes():
    n_clubs = p_int('Number of clubs, or blank to stop', allow_blank=True)
    while n_clubs:
        dupes, output = find_dupes(int(n_clubs))
        n = n_assignments(int(n_clubs))
        print(f'{n_clubs} clubs\n{n} assignments\n{len(dupes)} dupes\n')

        print(dupes)
        print()
        print(output)
        
        n_clubs = p_int('\nNumber of clubs, or blank to stop', allow_blank=True)

def program_dupes_r2():
    n_clubs = p_int('Number of clubs, or blank to stop', allow_blank=True)
    while n_clubs:
        runs = find_dupes_r2(int(n_clubs))
        for (kind, n) in runs:
            print(kind, n)
        
        n_clubs = p_int('\nNumber of clubs, or blank to stop', allow_blank=True)

def program_save_dupes():

    lower = p_int('From this number of clubs')
    upper = p_int('Up to and including this number of clubs')

    i_to_dupes = {}

    for i in range(lower, upper + 1):
        dupes, output = find_dupes(i)
        n = n_assignments(int(i))

        i_to_dupes[i] = dupes

        fname = f'dupes_{str(i).zfill(2)}'
        with open(f'./output/{fname}.txt', 'w') as f:            
            f.write(f'{i} clubs\n')
            f.write(f'{n} assignments\n')
            f.write(f'{len(dupes)} dupes\n\n')
            f.write(str(dupes) + '\n\n')
            f.write(output)

    with open(f'./output/_dupes_summary.csv', 'w') as f:
        f.write(','.join(list(str(i) for i in range(lower, upper + 1))) + '\n')
        longest = max(i_to_dupes.values(), key=len)

        keys = sorted(i_to_dupes.keys())
        for row in range(len(longest)):
            line = []
            for n_clubs in keys:
                dupes = i_to_dupes[n_clubs]
                if row < len(dupes):
                    line.append(str(dupes[row]))
                else:
                    line.append('')
            f.write(','.join(line) + '\n')



def program_assignments_set():
    n_clubs = p_int('Number of clubs, or blank to stop', allow_blank=True)
    while n_clubs:
        sets = assignments_set(int(n_clubs))
        print(f'{len(sets)} possible assignments')

        if p_bool('Show them'):
            print(format_sets_of_blocks(sets))
        
        n_clubs = p_int('\nNumber of clubs, or blank to stop', allow_blank=True)

        

def format_sets_of_blocks(combos) -> str:
    result = ''

    combos_sorted = []
    for s in combos:
        combos_sorted.append(sorted(s, key=lambda s: (-len(s), s)))
    
    combos_sorted.sort()

    for s in combos_sorted:
        result += ' | '.join(s) + '\n'

    return result

def program_save():

    lower = p_int('From this number of clubs')
    upper = p_int('Up to and including this number of clubs')

    f_summary = open(f'./output/_summary.csv', 'w')
    f_summary.write(','.join(['Number of clubs', 'Number of assignments', 'Example assignment']) + '\n')

    for i in range(lower, upper + 1):
        sets = assignments_set(i)
        formatted_blocks = format_sets_of_blocks(sets)

        f_summary.write(','.join([str(i), str(len(sets)), formatted_blocks.split('\n', 2)[0]]) + '\n')

        fname = str(i).zfill(2)
        with open(f'./output/{fname}.txt', 'w') as f:
            f.write(f'{i} clubs\n')
            f.write(f'{len(sets)} possible assignments\n\n')
            f.write(formatted_blocks)
    
    f_summary.close()

def assignments_yield_no_islice(n_clubs: int) -> Iterator[set]:

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

    def _is_good_row(i: int) -> int:
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
                next_run = next(runs)
                run[0], run[1] = next_run
                return _is_good_row(i)
            except:
                return -1

    def _illegal(block: set) -> bool:
        return any(co.issubset(block) for co in NO_COMBOS)
                
    choices = set(range(n_clubs))

    i = 1
    runs = _get_runs()
    run = next(runs)

    combinations_1 = islice(combinations(choices, n_block_1), 0, None)
        
    for block_1 in combinations_1:
        _c = _is_good_row(i)
        if _c == -1:
            return
        elif _c == 0:
            i += 1
            continue

        rest_2 = choices.difference(block_1)
        combinations_2 = combinations(rest_2, n_block_2)

        for block_2 in combinations_2:
            _c = _is_good_row(i)
            if _c == -1:
                return
            elif _c == 0:
                i += 1
                continue

            _c = _is_good_row(i)
            if _c == -1:
                return
            elif _c == 0:
                i += 1
                continue

            block_3 = rest_2.difference(block_2)

            i += 1
            yield (block_1, block_2, block_3)
            # yield set((''.join(block_1), ''.join(block_2), ''.join(block_3)))


def assignments_custom(n_clubs: int) -> Iterator[list]:

    distinct = set()

    def _yield(a: str, b: str, c: str):
        sig = frozenset((''.join(sorted(a)), ''.join(sorted(b)), ''.join(sorted(c))))
        if sig not in distinct:
            distinct.add(sig)
            return sig

    def _sub(choices: str) -> Iterator[list]:
        if len(choices) < 3:
            return

        if len(choices) == 3:
            yield [c for c in choices]

        elif len(choices) % 3 == 0:
            new = choices[-1]
            t = (len(choices) // 3) - 1
            for s in _sub(choices[:-1]):
                s = tuple(s)

                if len(s[0]) == t:
                    y = _yield(s[0] + new, s[1], s[2])
                    if y:
                        yield y
                elif len(s[1]) == t:
                    y = _yield(s[0], s[1] + new, s[2])
                    if y:
                        yield y
                else:
                    y = _yield(s[0], s[1], s[2] + new)
                    if y:
                        yield y
                
        elif len(choices) % 3 == 1:
            for i in range(len(choices)):
                sub_choices = choices[:i] + choices[i + 1:]
                new = choices[i]
                for s in _sub(sub_choices):
                    s = tuple(s)

                    y = _yield(s[0] + new, s[1], s[2])
                    if y:
                        yield y
                    
                    y = _yield(s[0], s[1] + new, s[2])
                    if y:
                        yield y
                    
                    y = _yield(s[0], s[1], s[2] + new)
                    if y:
                        yield y

        elif len(choices) % 3 == 2:

            # This is wrong... it only works for n=5...

            new = choices[-1]
            t = len(choices) // 3
            for s in _sub(choices[:-1]):
                s = tuple(s)
                shortest = [0, 1, 2]
                for i in range(3):
                    if len(s[i]) > t:
                        longest = shortest.pop(i)
                        break
                
                y = _yield(s[shortest[0]] + new, s[shortest[1]], s[longest])
                if y:
                    yield y
                
                y = _yield(s[shortest[0]], s[shortest[1]] + new, s[longest])
                if y:
                    yield y

                y = _yield(s[shortest[0]] + s[shortest[1]], s[longest], new)
                if y:
                    yield y

    for s in _sub(CHARSET[:n_clubs]):
        yield s


def program_assignments_custom(n_clubs: int=0, silent: bool=False):

    def _sub(n_clubs: int) -> None:
        sets = assignments_custom(int(n_clubs))
        n = n_assignments(int(n_clubs))
        print(f'{n_clubs} clubs / theoretical total {n:,}')

        if p_bool(f'Loop through them'):
            total = 0
            start = time.time()
            for s in sets:
                # s = tuple(s)

                # print(' | '.join(f'{b:<3}' for b in s))

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
