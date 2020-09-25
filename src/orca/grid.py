BANG_GLYPH = "*"
CURSOR_GLYPH = "@"
CROSS_GLYPH = "+"
DOT_GLYPH = "."
COMMENT_GLYPH = "#"
EMPTY_GLYPH = " "

GLYPH_TABLE = [
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "a",
    "b",  #  0-11
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",  # 12-23
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",  # 24-35
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


class OrcaGrid:
    """The internal orca grid representation.

    It keeps track of the internal grid state, the locks.
    """

    @classmethod
    def from_string(cls, s):
        lines = s.splitlines()
        if len(lines) > 200:
            raise ValueError(f"String has too many lines ({len(lines)}, max is 200)")

        if len(lines) < 1:
            raise ValueError(f"Empty string !")

        n = len(lines[0])
        for i, line in enumerate(lines):
            if len(line) != n:
                raise ValueError(f"Line {i} length is inconsistent: {len(line)} vs {n}")

        lines = [list(line) for line in lines]

        ret = cls(len(lines), len(lines[0]))
        ret._state = lines
        return ret

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

        # Raw state of the grid at a given state
        self._state = [[DOT_GLYPH for _ in range(cols)] for _ in range(rows)]

        # Each grid's position may be locked, in which case it should not be
        # processed as an operator. For example, if the right operator of add
        # is itself a letter, you want to make sure you're not considering it
        # as its own operator. Here we rely on orca processing from the left to
        # the right, and from the top to the bottom.
        self._locks = None

        self.reset_locks()

    def reset_locks(self):
        """ Reset locks.

        Every internal lock will be set as unlock.
        """
        self._locks = [
            [False for _ in range(self.cols)]
            for _ in range(self.rows)
        ]

    def peek(self, x, y):
        """Returns the glyph at the given indices.

        Will return empty string if outside the grid boundaries.
        """
        try:
            return self._state[y][x]
        except IndexError:
            return None

    def poke(self, x, y, value):
        """ Will set the given value at the given position in the grid.

        Will do nothing if outside the grid boundaries.
        """
        try:
            self._state[y][x] = value
        except IndexError:
            pass

    # Orca-compat 'layer', to help porting from orca nodejs code.
    def glyph_at(self, x, y):
        return self.peek(x, y)

    def value_at(self, x, y):
        return glyph_to_value(self.peek(x, y))

    def value_of(self, g):
        return glyph_to_value(g)
