from abc import ABC, abstractmethod

class SearchProblem(ABC):
    @abstractmethod
    def initial_state(self): pass

    @abstractmethod
    def is_goal(self, state): pass

    @abstractmethod
    def successors(self, state): pass

    @abstractmethod
    def hashable_state(self, state): pass