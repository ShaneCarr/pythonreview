
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

class BoatSide(Enum):
    LEFT = 0
    RIGHT = 1

class Side(NamedTuple):
    missionaries:int
    cannibals:int

def solve(left: Side, right: Side, side: BoatSide, path: List[Tuple[Side, Side, BoatSide]]):
    current = [[left], [right]]
    #check path to see if we visited this already
    if current in path:
        return False

    # check left to  see if c > m return false
    if left.cannibals > left.missionaries or right.cannibals > right.missionaries:
        path += current
        return False

    if left.cannibals == 0 and left.missionaries == 0:
        print("Found result")
        for step in path:
            left, right, boat = step
            print(f"Left: {left}, Right: {right}, Boat on: {boat.name}")
        return True

    path += current

    # on the left since we are moving right
    if side == BoatSide.LEFT:
        # move one or two from left to right.
        # options move case L->R: 1c-1m,2c,2m, c, m
        transferC = min(left.cannibals, 1)
        transferM = min(left.missionaries, 1)

        left_1 = left
        right_1 = right

        left_1.missionaries -= transferM
        right_1.missionaries += transferM

        left_1.cannibals -= transferC
        right_1.cannibals += transferC

        solve(left_1, right_1, BoatSide.RIGHT, path)

        left_2 = left
        right_2 = right

        transferC = min(left.cannibals, 2)

        left_2.cannibals -= transferC
        right_2.cannibals += transferC

        solve(left_2, right_2, BoatSide.RIGHT, path)

        left_3 = left
        right_3 = right

        transferm = min(left.missionaries, 2)

        left_3.missionaries -= transferm
        right_3.missionaries += transferm

        solve(left_3, right_3, BoatSide.RIGHT, path)

    if side == BoatSide.RIGHT:
        return True



    solve(left[0], right[0], side + 1, path)
    # check right to  see if c > m return false

    # check right to see if the values are 3,3




    # call solve transfering right to left or left to right dephding on what side boat is on.

    return True



if __name__ == '__main__':
    # tuples are m,c
    solve([3,3], [0,0], 0, 0, [])

