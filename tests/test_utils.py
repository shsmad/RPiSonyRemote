from utils import circular_increment  # assuming the utils.py is in the same directory


def test_increment_zero_range():
    # Test increment with zero range
    assert circular_increment(3, 1, 1, 1) == 1
    assert circular_increment(2, 7, 7, 3) == 7
    assert circular_increment(4, 0, 0, 2) == 0


def test_increment_within_range():
    # Test increment within the range
    assert circular_increment(3, 1, 5, 2) == 5
    assert circular_increment(2, 2, 5, 3) == 5
    assert circular_increment(4, 1, 5, 1) == 5


def test_increment_exceeding_range():
    # Test increment exceeding the range
    assert circular_increment(3, 1, 5, 4) == 2
    assert circular_increment(2, 1, 5, 6) == 3
    assert circular_increment(4, 1, 5, 5) == 4
