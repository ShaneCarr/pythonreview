class Jug:
    def __init__(self, capacity):
        self._capacity = capacity
        self.current = 0

    @property
    def capacity(self):
        return self._capacity

    def fill(self):
        self.current  = self.capacity

    def empty(self):
        self.current = 0

    def pour_into(self, other):
        amount = min(self.capacity, (other.capacity-other.current))
        other.current += amount
        self.current -= amount
