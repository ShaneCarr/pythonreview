
"""
Missionaries and Cannibals Problem
----------------------------------

- There are 3 missionaries and 3 cannibals on one side of a river.
- They all need to cross to the other side using a boat.
- The boat can carry either 1 or 2 people at a time.
- At no time, on either side of the river, can the number of cannibals
  exceed the number of missionaries — unless there are zero missionaries
  on that side.

  (If cannibals outnumber missionaries on a side, the missionaries
  would be eaten.)

Goal:
- Move all 3 missionaries and 3 cannibals safely to the other side
  of the river without violating the rules above.
"""
from typing import NamedTuple, List, Tuple
from enum import Enum
from dataclasses import dataclass
class BoatSide(Enum):
    LEFT = 0
    RIGHT = 1

@dataclass
class Side:
    missionaries:int
    cannibals:int

def move(source: Side, destination: Side, cannibals: int, missionary: int) -> Tuple[Side, Side]:
    move_canbibals = min(cannibals, source.cannibals)
    source.cannibals -= move_canbibals
    destination.cannibals += cannibals

    move_missionaries = min(missionary, source.missionaries)
    source.missionaries -= move_missionaries
    destination.missionaries += move_missionaries

    return source, destination

def solve(left: Side, right: Side, path: List[Tuple[Side, Side]]):
    current = [[left], [right]]
    #check path to see if we visited this already
    if current in path:
        return False

    # on either side cannibals can't be great than missionaries.
    if left.cannibals > left.missionaries or right.cannibals > right.missionaries:
        path += current
        return False

    # moved everyone from left to right. so left needs to be 0
    if left.cannibals == 0 and left.missionaries == 0:
        print("Found result")
        for step in path:
            left, right = step
            print(f"Left: {left}, Right: {right}")
        return True

    path += current

    left_after, right_after = move(left, right, 1, 1)
    solve(left_after, right_after, path)

    left_after, right_after = move(left, right, 2, 0)
    solve(left_after, right_after, path)

    left_after, right_after = move(left, right, 0, 2)
    solve(left_after, right_after, path)

    left_after, right_after = move(left, right, 1, 0)
    solve(left_after, right_after, path)

    left_after, right_after = move(left, right, 0, 1)
    solve(left_after, right_after, path)

    return False

if __name__ == '__main__':
    # tuples are m,c
    left = Side(missionaries=3, cannibals=3)
    right = Side(missionaries=0, cannibals=0)
    solve(left, right, [])

