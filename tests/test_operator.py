import math
import unittest

from orca.grid import OrcaGrid
from orca.operators import Add, Clock


O = OrcaGrid.from_string


class TestAddOperator(unittest.TestCase):
    def test_operation(self):
        # Given
        grid = O("1A2\n...")
        add = Add(grid, 1, 0)

        # When
        payload = add.operation(0)

        # Then
        assert payload == "3"

        # Given
        grid = O(".A2\n...")
        add = Add(grid, 1, 0)

        # When
        payload = add.operation(0)

        # Then
        assert payload == "2"

        # Given
        grid = O("1Ab\n...")
        add = Add(grid, 1, 0)

        # When
        payload = add.operation(0)

        # Then
        assert payload == "c"

        # Given
        grid = O("1AB\n...")
        add = Add(grid, 1, 0)

        # When
        payload = add.operation(0)

        # Then
        assert payload == "c"


class TestClockOperator(unittest.TestCase):
    def test_operation(self):
        # Given
        grid = O(f".C.\n...")
        clock = Clock(grid, 1, 0)

        # When
        for frame in range(10):
            payload = clock.operation(frame)
            # Then
            assert payload == str(frame % 8)

        # Given
        mod = 4
        grid = O(f".C{mod}\n...")
        clock = Clock(grid, 1, 0)

        # When
        for frame in range(10):
            payload = clock.operation(frame)
            # Then
            assert payload == str(frame % mod)

        # Given
        mod = 4
        rate = 3
        grid = O(f"{rate}C{mod}\n...")
        clock = Clock(grid, 1, 0)

        # When
        for frame in range(20):
            payload = clock.operation(frame)
            # Then
            assert payload == str(math.floor(frame / rate) % mod)
