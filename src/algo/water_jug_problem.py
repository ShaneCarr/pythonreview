def solve(x, y, jug_a, jug_b, goal, path):
    print (f"visiting ({x}, {y})")

    if x == goal or y == goal:
        print("GOAL REACHED!")
        for step in path:
            print(step)
            print(f"Final state: ({x}, {y})")
        return True

    # we've already searched this path.
    if (x, y) in path:
        return False

    path = path + [(x, y)]

    # Try to pour A -> B
    # transfer: how much can be poured
    transfer = min(x, jug_b - y)
    if solve(x - transfer, y + transfer, jug_a, jug_b, goal, path):
        return True

    # empty B
    if solve(x, 0, jug_a, jug_b, goal, path):
        return True

    # empty A
    if solve(0, y, jug_a, jug_b, goal, path):
        return True

    # fill A
    if solve(jug_a, y, jug_a, jug_b, goal, path):
        return True

    # Transfer B->A (y or the space available)
    transfer = min(y, jug_a - x)
    if solve(x + transfer, y - transfer, jug_a, jug_b, goal, path):
        return True

    return False


if __name__ == "__main__":
    jug_a = 4
    jug_b = 3
    goal = 2

    # start with 0 in each jug
    solve(0,0, jug_a, jug_b, goal, [])
