BANG_GLYPH = "*"
CURSOR_GLYPH = "@"
CROSS_GLYPH = "+"
DOT_GLYPH = "."
COMMENT_GLYPH = "#"
EMPTY_GLYPH = " "

GLYPH_TABLE = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', #  0-11
    'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', # 12-23
    'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', # 24-35
]
GLYPH_TABLE_SIZE = len(GLYPH_TABLE)
INDEX_TO_GLYPH = {k: i for i, k in enumerate(GLYPH_TABLE)}


# orca-c has a different version
def index_of_orca_js(c):
    return INDEX_TO_GLYPH.get(c.lower(), -1)


glyph_table_index_of = index_of_orca_js


def glyph_to_value(glyph):
    if glyph in (DOT_GLYPH, BANG_GLYPH, None, ""):
        return 0
    else:
        return glyph_table_index_of(glyph)
