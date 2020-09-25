import unittest

from hypothesis import given
from hypothesis.strategies import characters, sampled_from

from orca.grid import GLYPH_TABLE, DOT_GLYPH, BANG_GLYPH, glyph_to_value, OrcaGrid


# This contains the list of glyph that will give back a value.
#
# We order to have a stable ordered list, but we actually don't care about the
# exact order
GLYPH_WITH_VALUE = sorted(set(GLYPH_TABLE) | set(c.upper() for c in GLYPH_TABLE))
SPECIAL_GLYPHS = [DOT_GLYPH, BANG_GLYPH, None, ""]


@given(sampled_from(GLYPH_WITH_VALUE))
def test_glyph_to_value_acceptable(c):
    value = glyph_to_value(c)
    assert value >= 0
    assert value < 36


@given(sampled_from(GLYPH_WITH_VALUE))
def test_glyph_to_value_upper_lower(c):
    assert glyph_to_value(c.lower()) == glyph_to_value(c.upper())


@given(characters())
def test_glyph_to_value_unexpected(c):
    value = glyph_to_value(c)
    assert value >= -1
    assert value < 36


@given(sampled_from(SPECIAL_GLYPHS))
def test_glyph_to_value_special(c):
    assert glyph_to_value(c) == 0


def test_create_grid_from_string_simple(self):
    # Given
    s = "...\n..."

    # When
    grid = OrcaGrid.from_string(s)

    # Then
    assert grid.rows == 2
    assert grid.cols == 3


def test_create_grid_from_string_simple():
    # Given
    s = "...\n..."

    # When
    grid = OrcaGrid.from_string(s)

    # Then
    assert grid.rows == 2
    assert grid.cols == 3


O = OrcaGrid.from_string


class TestGridPeekAndPoke(unittest.TestCase):
    def test_peek_in_bounds(self):
        # Given
        grid = O(".A.\n...")

        # When
        glyph = grid.peek(0, 0)

        # Then
        assert glyph == DOT_GLYPH

        # When
        glyph = grid.peek(1, 0)

        # Then
        assert glyph == "A"

    def test_peek_out_of_bounds(self):
        # Given
        grid = O(".A.\n...")

        # When
        glyph = grid.peek(4, 4)

        # Then
        assert glyph is None

    def test_poke(self):
        # Given
        grid = O(".A.\n...")

        # When
        glyph = grid.peek(1, 1)

        # Then
        assert glyph == DOT_GLYPH

        # When
        grid.poke(1, 1, "3")
        glyph = grid.peek(1, 1)

        # Then
        assert glyph == "3"

    def test_poke_out_bounds(self):
        # Given
        grid = O(".A.\n...")

        # When
        grid.poke(3, 3, "3")
        glyph = grid.peek(3, 3)

        # Then
        assert glyph is None


class TestGridCompatLayer(unittest.TestCase):
    def test_glyph_at(self):
        # Given
        grid = O(".A.\n...")

        # When
        glyph = grid.glyph_at(0, 0)

        # Then
        assert glyph == DOT_GLYPH

        # When
        glyph = grid.glyph_at(1, 0)

        # Then
        assert glyph == "A"

    @given(sampled_from(SPECIAL_GLYPHS))
    def test_value_of(self, c):
        # Given
        grid = O(".")

        # When
        value = grid.value_of(c)

        # Then
        assert value == 0

    def test_value_at(self):
        # Given
        grid = O("3")

        # When
        value = grid.value_at(0, 0)

        # Then
        assert value == 3

        # When
        value = grid.value_at(0, 3)

        # Then
        assert value == 0

        # When
        value = grid.value_at(-2, 1)

        # Then
        assert value == 0
