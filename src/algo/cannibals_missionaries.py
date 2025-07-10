
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
import copy

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

@dataclass(frozen=True)
class State:
    left: Side
    right: Side
    boat_side: BoatSide

def move(l: Side, r: Side, cannibals: int, missionary: int, side: BoatSide, path: List[Tuple[Side, Side, BoatSide]]) -> Tuple[Side, Side, BoatSide]:
    lcone = copy.deepcopy(l)
    rclone = copy.deepcopy(r)

    # keep math single set, and generic. Easier to add more properties
    # sicne we likely won't add new sides. but that can be changed
    if side == BoatSide.LEFT:
        source  = lcone
        destination = rclone
        side = BoatSide.RIGHT
    else:
        source = rclone
        destination = lcone
        side = BoatSide.LEFT

    move_canbibals = min(cannibals, source.cannibals)
    source.cannibals -= move_canbibals
    destination.cannibals += move_canbibals

    move_missionaries = min(missionary, source.missionaries)
    source.missionaries -= move_missionaries
    destination.missionaries += move_missionaries

    # convert back to left and right for easy checking since the state is based on left and right
    return lcone, rclone, side


def check_move(l: Side, r: Side, side: BoatSide, path: List[Tuple[Side, Side, BoatSide]]) -> bool:
    if l.missionaries == 0 and l.cannibals == 0 and side == BoatSide.RIGHT:
        print("Found result")
        for step in path:
            solve_left, solve_right, side = step
            print(f"Left: {solve_left}, Right: {solve_right}, Side: {side}")
        return True
    return False


def solve(l: Side, r: Side, path: List[Tuple[Side, Side, BoatSide]], side: BoatSide):
    left_solve = copy.deepcopy(l)
    right_solve = copy.deepcopy(r)
    current = copy.deepcopy((left_solve, right_solve, side))
    side_solve = copy.deepcopy(side)

    #check path to see if we visited this already
    if current in path:
        return False

    path.append(current)

    # on either side cannibals can't be great than missionaries.
    if  (left_solve.cannibals > left_solve.missionaries > 0) or (right_solve.cannibals > right_solve.missionaries > 0):
        path.append(current)
        return False

    left_after, right_after, next_side = move(left_solve, right_solve, 1, 1, side_solve, path)
    if check_move(left_after, right_after, next_side, path):
        print("Found result") # todo i can return here if i don't want to see all results

    solve(left_after, right_after, path, next_side)

    left_after, right_after, next_side = move(left_solve, right_solve, 2, 0, side_solve, path)
    if check_move(left_after, right_after, next_side, path):
        print("Found result") # todo i can return here if i don't want to see all results

    solve(left_after, right_after, path, next_side)

    left_after, right_after, next_side = move(left_solve, right_solve, 0, 2, side_solve, path)
    if check_move(left_after, right_after, next_side, path):
        print("Found result") # todo i can return here if i don't want to see all results

    solve(left_after, right_after, path, next_side)

    left_after, right_after, next_side = move(left_solve, right_solve, 1, 0, side_solve, path)
    if check_move(left_after, right_after, next_side, path):
        print("Found result") # todo i can return here if i don't want to see all results

    solve(left_after, right_after, path, next_side)

    left_after, right_after, next_side = move(left_solve, right_solve, 0, 1, side_solve, path)
    if check_move(left_after, right_after, next_side, path):
        print("Found result") # todo i can return here if i don't want to see all results

    solve(left_after, right_after, path, next_side)

    return False

if __name__ == '__main__':
    # tuples are m,c
    left = Side(missionaries=3, cannibals=3)
    right = Side(missionaries=0, cannibals=0)
    solve(left, right, [], BoatSide.LEFT)

