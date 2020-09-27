import math
import unittest

from orca.grid import OrcaGrid
from orca.operators import Add, Clock, Generator, Increment, Substract


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


class TestSubstractOperator(unittest.TestCase):
    def test_operation(self):
        # Given
        grid = O("0B2\n...")
        sub = Substract(grid, 1, 0)

        # When
        payload = sub.operation(0)

        # Then
        assert payload == "2"

        # Given
        grid = O("1B4\n...")
        sub = Substract(grid, 1, 0)

        # When
        payload = sub.operation(0)

        # Then
        assert payload == "3"


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


class TestGeneratorOperator(unittest.TestCase):
    def test_operation(self):
        # given
        grid = O(f".0.GE\n.....\n.....")
        gen = Generator(grid, 3, 0)

        # when
        gen.operation(0)

        # then
        assert grid.peek(3, 1) == "E"

        # given
        grid = O(f".1.GE\n.....\n.....")
        gen = Generator(grid, 3, 0)

        # when
        gen.operation(0)

        # then
        assert grid.peek(3, 2) == "E"


class TestIncrementOperator(unittest.TestCase):
    def test_operation(self):
        # given
        grid = O(f"..I4.\n.....")
        inc = Increment(grid, 2, 0)

        # when
        payload = inc.operation(0)

        # then
        assert payload == "1"

        # given
        grid = O(f"..I4.\n..2..")
        inc = Increment(grid, 2, 0)

        # when
        payload = inc.operation(0)

        # then
        assert payload == "3"
