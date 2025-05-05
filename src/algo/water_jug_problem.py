from src.core.search_problem import SearchProblem


class WaterJugProblem(SearchProblem):
    def __init__(self, cap1, cap2, goal):
        self.cap1 = cap1
        self.cap2 = cap2
        self.goal = goal

    def initial_state(self):
        return 0, 0

    def is_goal(self, state):
        return self.goal in state

    # this allow the value to be stuck in has table
    def hashable_state(self, state):
        return tuple(state)

    # this is like advance
    def successor(self, state):
        x,y = state
        cap1 = self.cap1
        cap2 = self.cap2
        result = []

        def add(new_x, new_y, action):
            print(f"Generating: ({new_x} {new_y} via {action})")
            result.append((new_x, new_y, action))

