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
from enum import Enum
from lib.decorator import pass_by_value

class BoatSide(Enum):
    LEFT = "left"
    RIGHT = "right"

class Side:
    cannibals: int
    missionaries: int

    def __init__(self, cannibals: int, missionaries: int):
        self.cannibals = cannibals
        self.missionaries = missionaries

class GameState:
    left: Side
    right: Side
    boat_Side: BoatSide
    def __init__(self, left: Side, right: Side, boat_side: BoatSide):
        self.left = left
        self.right = right
        self.boat_side = boat_side

class BoatContents:
    cannibals: int
    missionaries: int
    def __init__(self, cannibals: int, missionaries: int):
        self.cannibals = cannibals
        self.missionaries = missionaries

@pass_by_value
def move(state: GameState,  boatContents: BoatContents):
    # make generic concepts of source and destination for move.
    source = state.left
    destination = state.right

    if state.boat_Side == BoatSide.RIGHT:
        source = state.right
        destination = state.left

        # conceptually reset the boat location, so we alternate the boat locations (moving path back and forth)
        # until we run out of or find a solution.
        state.boat_Side = BoatSide.LEFT

    # calculate the source destinaton change, and change the "side"
    source.cannibals -= boatContents.cannibals
    destination.cannibals += boatContents.cannibals

    source.missionaries -= boatContents.missionaries
    destination.missionaries += boatContents.missionaries

if __name__ == "__main__":
    print("starting")
