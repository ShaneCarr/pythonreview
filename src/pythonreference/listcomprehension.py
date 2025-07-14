from typing import List

from src.algo.canniabls_missionaries import BoatContents

min_capacity : int = 1
max_capacity : int = 2
def generate_combinations() -> List[BoatContents]:
    return [BoatContents(c, m)
            for c in range(min_capacity, max_capacity + 1)
            for m in range(min_capacity, max_capacity + 1)]