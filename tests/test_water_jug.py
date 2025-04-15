from src.algo.water_jug import solve_water_jug

def test_basic():
    assert solve_water_jug(3, 5,4) is not None
