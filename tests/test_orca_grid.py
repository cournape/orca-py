import unittest

from hypothesis import given
from hypothesis.strategies import characters, sampled_from

from orca.grid import GLYPH_TABLE, DOT_GLYPH, BANG_GLYPH, glyph_to_value


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
