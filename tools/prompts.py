# import levels

YES = 'y'
NO = 'n'
INDENT = '    '
NAME_CHARS = (' ', ',', '-', '.')

# ==============================================================================
# I/O
# ==============================================================================

def in_print(s: str, indent: int=0):
    print(f'{INDENT * indent}{s}')

def in_prompt(s: str, indent: int=0):
    return input(f'{INDENT * indent}{s}: ').strip()

def invalid(s: str, indent: int=0):
    in_print(f'Invalid: {s}\n', indent)

# ==============================================================================
# VALIDATORS
# ==============================================================================

def v_nonempty(choice: str) -> bool:
    return choice.strip() != ''

def v_name(choice: str) -> bool:
    """Return True if the given str is alphabetic besides OKAY characters."""
    sanitized = choice
    for char in NAME_CHARS:
        sanitized = sanitized.replace(char, '')        
    return sanitized.isalpha()

def v_str(choice: str, lower: int=1, upper: int=float('inf')) -> bool:
    return lower <= len(choice) <= upper

def v_number(choice: str, converter: callable, lower: float, upper: float) -> bool:
    try:
        return lower <= converter(choice) <= upper
    except:
        return False

def v_int(choice: str, lower: int=float('-inf'), upper: int=float('inf')) -> bool:
    return v_number(choice, int, lower, upper)

def v_float(choice: str, lower: int=float('-inf'), upper: int=float('inf')) -> bool:
    return v_number(choice, float, lower, upper)

def v_bool(choice: str, strict: bool=False) -> bool:
    choice = choice.lower()
    return (not strict) or (v_nonempty(choice) and (choice in (YES, NO)))

def v_level(choice: str) -> bool:
    return levels.is_valid_level(choice)

def v_grade(choice: str) -> bool:
    choice = choice.strip('%')
    return v_float(choice) and levels.is_valid_grade(float(choice))

# ==============================================================================
# PROMPTS
# ==============================================================================

def p(p: str='Input',  indent: int=0, validators: list=[], inv: str='', allow_blank: bool=False, args: list=[], kwargs: dict={}):

    choice = in_prompt(p, indent)
    while (not (allow_blank and (not choice.strip()))) and (not all(v(choice, *args, **kwargs) for v in validators)):
        invalid(inv, indent)
        choice = in_prompt(p, indent)
    return choice.strip()

def p_bool(prompt: str='Yes or no', indent: int=0, strict: bool=False, default: bool=True, allow_blank: bool=False) -> bool:
    """
    Prompt yes/no and return a bool.
    If a default is given, only give the non-default if it's explicitly input.
    In strict mode, only return True/False; None is not possible.
    If not strict and no default, any input besides yes/no returns None.
    """
        
    choice = p(f'{prompt}? {YES}/{NO}', indent, [v_bool], f'{YES} or {NO}', [strict])
    choice = choice.lower()

    if allow_blank and (not choice.strip()):
        return default

    if default is True:
        return choice != NO
    elif default is False:
        return choice == YES
    else:
        return True if choice == YES else False if choice == NO else None

def p_name(prompt: str='Name', indent: int=0, allow_blank: bool=False) -> str:
    choice = p(prompt, indent, [v_nonempty, v_name], f'letters + {NAME_CHARS}', allow_blank=allow_blank)
    return choice

def p_str(prompt: str='String', indent: int=0, lower: int=1, upper: int=float('inf'), allow_blank: bool=False) -> str:
    choice = p(prompt, indent, [v_str], f'between {lower} and {upper} characters', allow_blank=allow_blank, args=[lower, upper])
    return choice

def p_int(prompt: str='Integer', indent: int=0, lower: int=float('-inf'), upper: int=float('inf'), allow_blank: bool=False) -> int:
    inv = f'integer between {lower} and {upper} (inclusive)'
    choice = p(prompt, indent, [v_int], inv, allow_blank=allow_blank, args=[lower, upper])
    return int(choice) if choice else None

def p_float(prompt: str='Number', indent: int=0, lower: float=float('-inf'), upper: float=float('inf'), allow_blank: bool=False) -> float:
    inv = f'number between {lower} and {upper} (inclusive)'
    choice = p(prompt, indent, [v_float], inv, allow_blank=allow_blank, args=[lower, upper])
    return float(choice) if choice else None

def p_level(prompt: str='Level', indent: int=0, allow_blank: bool=False) -> str:
    choice = p(prompt, indent, [v_level], 'level in Growing Success', allow_blank=allow_blank).upper()
    return choice

def p_grade(prompt: str='Grade', indent: int=0, allow_blank: bool=False) -> float:
    choice = p(prompt, indent, [v_grade], '% from 0 to 120', allow_blank=allow_blank).strip('%')
    return float(choice) if choice else None

def p_choice(prompt: str='Options', choices=[], indent: int=0, allow_blank: bool=False) -> int:
    if not choices:
        raise Exception
    
    max_cols = len(str(len(choices)))
    
    choice_strs = []
    for (i, choice) in enumerate(choices):
        choice_strs.append(f'{str(i + 1).ljust(max_cols)}: {choice}')
    prompt = f'{prompt}:\n\n' + '\n'.join(choice_strs) + '\n\nChoice'
    
    return p_int(prompt, indent=indent, lower=1, upper=len(choices), allow_blank=allow_blank)

# ==============================================================================
# FORMATTING
# ==============================================================================

def f_float(f: float) -> str:
    truncated = f'{f:.1f}'
    rounded = f'{round(f, 1)}'
    return truncated if truncated == rounded else f'{truncated} or {rounded}'

# ==============================================================================
# OPERATIONS
# ==============================================================================

def loop(routine: callable, args: list=[], kwargs: dict={},
         blank_before: bool=True, blank_after: bool=True):
    responses = []
    go = p_bool('Start')
    while go:
        responses.append(routine(*args, **kwargs))
        if blank_before: print()
        go = p_bool('Continue')
        if blank_after: print()
    return responses
