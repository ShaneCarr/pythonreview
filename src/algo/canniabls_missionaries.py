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
from typing import List, Tuple, Optional, NamedTuple

from libs.decorator import pass_by_value

max_capacity: int = 2
min_capacity: int = 1

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
    boat_side: BoatSide
    total_cannibals: int
    total_missionaries: int
    path = List[Tuple[Side, Side, BoatSide]]
    has_more = True
    def __init__(self, left: Side, right: Side, boat_side: BoatSide, total_cannibals: int, total_missionaries: int):
        self.left = left
        self.right = right
        self.boat_side = boat_side
        self.total_cannibals = total_cannibals
        self.total_missionaries = total_missionaries
        self.path = []

class BoatContents:
    cannibals: int
    missionaries: int
    def __init__(self, cannibals: int, missionaries: int):
        self.cannibals = cannibals
        self.missionaries = missionaries

@pass_by_value
def move(state: GameState,  boatContents: BoatContents) -> GameState:
    # make generic concepts of source and destination for move.
    if state.boat_side == BoatSide.RIGHT:
        state.boat_Side = BoatSide.LEFT #boat needs to move boat directions each way it takes boat contents.
        state.has_more = calculate_edges(state.right, state.left, state, boatContents) # todo remove variables, debugging
    else: #left
        state.boat_side = BoatSide.RIGHT #boat needs to move boat directions each way it takes boat contents.
        state.has_more = calculate_edges(state.left, state.right, state, boatContents) # todo remove variables, debugging

    state.path.append((state.left, state.right, state.boat_side))
    return state

# pass by reference, returns should continue.
def calculate_edges(source: Side,
                    destination: Side,
                    state: GameState,
                    boat_contents: BoatContents, ) -> bool:
    state.has_more = True

    # this case is a dead end for this sub tree.
    if source.cannibals < boat_contents.cannibals:
        state.has_more = False
        print(f"INVALID MOVE - Not enough cannibals on source:")
        print(f"  Trying to move: {boat_contents.cannibals} cannibals")
        print(f"  Available on source: {source.cannibals} cannibals")
        print(f"  Shortfall: {boat_contents.cannibals - source.cannibals}")
        return False

    # this case is a dead end for this sub tree.
    if source.missionaries < boat_contents.missionaries:
        state.has_more = False
        print(f"INVALID MOVE - Not enough missionaries on source:")
        print(f"  Trying to move: {boat_contents.missionaries} missionaries")
        print(f"  Available on source: {source.missionaries} missionaries")
        print(f"  Shortfall: {boat_contents.missionaries - source.missionaries}")
        return False

    source.cannibals -= boat_contents.cannibals
    destination.cannibals += boat_contents.cannibals
    source.missionaries -= boat_contents.missionaries
    destination.missionaries += boat_contents.missionaries

    # the cannibals out number missionaries
    if ((source.missionaries > 0 and source.cannibals > source.missionaries) or
            (destination.missionaries > 0 and destination.cannibals > destination.missionaries)):
        state.has_more = False
        print(f"Win condition check:")
        print(f"  source.cannibals == 0: {source.cannibals == 0} (actual: {source.cannibals})")
        print(f"  destination.cannibals == 0: {destination.cannibals == 0} (actual: {destination.cannibals})")
        print(
            f"  destination.missionaries == total: {destination.missionaries == state.total_missionaries} (actual: {destination.missionaries}, expected: {state.total_missionaries})")
        print(
            f"  destination.cannibals == total: {destination.cannibals == state.total_cannibals} (actual: {destination.cannibals}, expected: {state.total_cannibals})")

    # everyone is moved. we got there w/o violating the above invalid cases.
    if (source.cannibals == 0 and source.missionaries == 0
            and destination.missionaries == state.total_missionaries
            and destination.cannibals == state.total_cannibals):
        state.has_more = False
        print(state.path)
        print("🎉" * 50)
        print("🏆 SOLUTION FOUND! 🏆")
        print("🎉" * 50)
        print(f"All {state.total_missionaries} missionaries and {state.total_cannibals} cannibals safely crossed!")
        print(f"Solution found in {len(state.path)} moves:")
        print("-" * 40)

        for i, move in enumerate(state.path, 1):
            print(f"Move {i}: {move}")

        print("-" * 40)
        print("✅ PUZZLE SOLVED!")
        print()
        return False
    return True

def generate_combinations() -> List[BoatContents]:
    boat_possibilities : List[BoatContents] = []
    for c in range(0, max_capacity):
        for m in range(0, max_capacity):
            if max_capacity >= c + m >= 1:
                boat_possibilities.append(BoatContents(c, m))
    return boat_possibilities

# i need something flatteded for cycle checking.
class StateSnapshot(NamedTuple):
    left_cannibals: int
    left_missionaries: int
    right_cannibals: int
    right_missionaries: int
    boat_side: BoatSide

def solve(state: GameState):
    # we need to move 1 or two at a time it's not possible to move zero
    # because who would be running the boat, unless the boat is a drone,
    # but that's not in the instructions above.
    boatContents_list = generate_combinations()
    for combination in boatContents_list:
        game_state = move(state, combination)
        has_visited :bool = False

        current = (state.left.cannibals,
                   state.right.missionaries,
                   state.right.cannibals,
                   state.left.missionaries,
                   state.boat_side)

        path_flattened = [StateSnapshot(l.cannibals, l.missionaries, r.cannibals, r.missionaries, b)
                          for l, r, b in state.path]

        # we visited this!
        if current in path_flattened:
            print("avoiding cycle")
            return

        if game_state.has_more:
            solve(game_state)

if __name__ == "__main__":
    print("starting")
    state = GameState(left=Side(missionaries=3, cannibals=3),
                      right=Side(missionaries=0, cannibals=0),
                      boat_side=BoatSide.LEFT,
                      total_cannibals=3,
                      total_missionaries=3)
    solve(state)
