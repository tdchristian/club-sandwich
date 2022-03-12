import random
import time

def distribute(numbers):
    boxes = [0, 0, 0]
    numbers.sort(reverse=True)
    for n in numbers:
        lowest = min(boxes)
        lowest_i = list(filter(lambda i: boxes[i] == lowest, [0, 1, 2]))[0]
        boxes[lowest_i] += n
    return boxes

def validate(numbers, boxes):
    boxes.sort()
    numbers.sort() # technically done above in reverse but whatever
    lower_two_diff = abs(boxes[1] - boxes[0])
    threshold = 2 * numbers[0]    
    return lower_two_diff < threshold, lower_two_diff, threshold

def generate_and_test():
    start = time.perf_counter()
    for i in range(10_000):
        numbers = []
        
        for _ in range(40):
            numbers.append(random.randint(1, 100))
            
        boxes = distribute(numbers)
        valid, diff, threshold = validate(numbers, boxes)
        if not valid:
            print(f'Invalid case: {boxes} ({diff:>2} >= {threshold:>2})')

        n = i + 1
        if n % 1000 == 0 or n == 10_000:
            dur = time.perf_counter() - start
            # meh too quick
            # print(f'{dur:.5f} seconds: Tested {n} cases')

generate_and_test()
