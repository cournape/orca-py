import pathlib


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
    "b",
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
    "n",
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
    "z",
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
    def from_path(cls, path):
        path = pathlib.Path(path)
        size = path.stat().st_size

        if size > 1024 ** 2:
            raise ValueError(f"File {path} too big.")

        with open(path, "rt") as fp:
            # We can read all in memory because we checked the file was not crazy
            # large
            return cls.from_string(fp.read())

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

    def iter_rows(self):
        return iter(self._state)

    # Locking utils
    def lock(self, x, y):
        self._locks[y][x] = True

    def is_operator_locked(self, operator):
        return self.is_locked(operator.x, operator.y)

    def is_locked(self, x, y):
        return self._locks[y][x]

    def reset_locks(self):
        """Reset locks.

        Every internal lock will be set as unlock.
        """
        self._locks = [[False for _ in range(self.cols)] for _ in range(self.rows)]

    # Peek/poke/listen
    def listen(self, port):
        """Listen to the given port.

        This essentially peeks at the given port's position, taking into
        account the port default.
        """
        g = self.peek(port.x, port.y)
        if g in (DOT_GLYPH, BANG_GLYPH) and port.default:
            return port.default
        else:
            return g

    def listen_as_value(self, port):
        """Listen to the given port's value.

        This listen to the port's glyph, and translates it into a numerical
        value, taking into account the port clamp.
        """
        glyph = self.listen(port)
        return port.clamp(self.value_of(glyph))

    def peek(self, x, y):
        """Returns the glyph at the given indices.

        Will return empty string if outside the grid boundaries.
        """
        try:
            return self._state[y][x]
        except IndexError:
            return None

    def poke(self, x, y, value):
        """Will set the given value at the given position in the grid.

        Will do nothing if outside the grid boundaries.
        """
        try:
            self._state[y][x] = value
        except IndexError:
            pass

    # Orca-compat 'layer', to help porting from orca nodejs code.
    def glyph_at(self, x, y):
        return self.peek(x, y)

    def key_of(self, index, upper_case=False):
        """ Returns the glyph from the given table index."""
        glyph = GLYPH_TABLE[index % GLYPH_TABLE_SIZE]
        if upper_case:
            return glyph.upper()
        else:
            return glyph

    def value_at(self, x, y):
        return glyph_to_value(self.peek(x, y))

    def value_of(self, g):
        return glyph_to_value(g)
