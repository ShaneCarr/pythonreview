import unittest

from src.algo.jug import Jug

class TestJug(unittest.TestCase):
    def test_fill(self):
        jug = Jug(4)
        jug.fill()
        self.assertEqual(jug.capacity, 4)

    def test_empty(self):
        jug = Jug(4)
        jug.fill()
        jug.empty()
        self.assertEqual(jug.current, 0)

    def test_pour(self):
        jug4 = Jug(4)
        jug4.fill()
        jug3 = Jug(3)

        jug4.pour_into(jug3)

        self.assertEqual(jug3.current, 3)
        self.assertEqual(jug4.current, 1)

if __name__ == '__main__':
    unittest.main()

