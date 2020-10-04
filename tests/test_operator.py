import math
import unittest

from orca.grid import OrcaGrid
from orca.operators import (
    IOperator,
    Add,
    Clock,
    Generator,
    Increment,
    Multiply,
    Substract,
)


O = OrcaGrid.from_string


class BaseOperator(IOperator):
    def operation(self):
        pass


class TestBaseOperator(unittest.TestCase):
    def test_has_neighbor(self):
        # Given
        grid = O("123\n4+6\n789")
        op = BaseOperator(grid, 1, 1, "base", "base op")

        # When/Then
        for diag in range(1, 10, 2):
            assert not op.has_neighbor(str(diag))

        # When/Then
        for diag in range(2, 10, 2):
            assert op.has_neighbor(str(diag))

    def test_move(self):
        # Given
        grid = O("+..\n...\n...")
        new_glyph = "本"
        offset_x, offset_y = 1, 2

        op = BaseOperator(grid, 0, 0, "base", "base op", glyph=new_glyph)

        # When
        op.move(offset_x, offset_y)

        # Then
        assert grid.peek(offset_x, offset_y) == new_glyph


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


class TestMultiplyOperator(unittest.TestCase):
    def test_operation(self):
        # Given
        grid = O("2M2\n...")
        m = Multiply(grid, 1, 0)

        # When
        payload = m.operation(0)

        # Then
        assert payload == "4"

        # Given
        grid = O(".M2\n...")
        m = Multiply(grid, 1, 0)

        # When
        payload = m.operation(0)

        # Then
        assert payload == "0"

        # Given
        grid = O("3MB\n...")
        m = Multiply(grid, 1, 0)

        # When
        payload = m.operation(0)

        # Then
        assert payload == "x"

        # Given
        grid = O("2Ma\n...")
        m = Multiply(grid, 1, 0)

        # When
        payload = m.operation(0)

        # Then
        assert payload == "k"
