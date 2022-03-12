def assignments_yield_islice(n_clubs: int) -> Iterator[set]:
    # This is almost but not quite accurate
    # It's about 15% faster than non-islice, but I can't get the combinators to roll over right

    n_block_1 = n_clubs // 3 + ((n_clubs % 3) > 0)
    n_block_2 = n_clubs // 3 + ((n_clubs % 3) > 1)

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
                
    # for block_1 in combinations(choices, n_block_1):
    #     rest_2 = choices.difference(block_1)
    #     for block_2 in combinations(rest_2, n_block_2):
    #         yield block_1, block_2, rest_2.difference(block_2)
    # print('\n\n')

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