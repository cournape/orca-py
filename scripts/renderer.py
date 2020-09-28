import argparse
import contextlib
import curses
import logging
import sys

from orca.grid import BANG_GLYPH, DOT_GLYPH, EMPTY_GLYPH, OrcaGrid


logger = logging.getLogger(__name__)


@contextlib.contextmanager
def noecho():
    curses.noecho()
    yield
    curses.echo()


@contextlib.contextmanager
def keypad(screen):
    screen.keypad(True)
    yield
    screen.keypad(False)


@contextlib.contextmanager
def cbreak():
    curses.cbreak()
    yield
    curses.nocbreak()


def init_colors():
    # TODO: implement basic colors etup
    pass


from orca.operators import Add, Bang, Clock, East, Generator, Increment, Substract, Midi

_CHAR_TO_OPERATOR_CLASS = {
    "a": Add,
    "b": Substract,
    "c": Clock,
    "e": East,
    "g": Generator,
    "i": Increment,
    BANG_GLYPH: Bang,
    ":": Midi,
    # COMMENT_GLYPH: Comment,
}


def operator_factory(grid, grid_char, x, y):
    """Factory for operators.

    Note: it will return None if no Operator class is found.
    """
    klass = _CHAR_TO_OPERATOR_CLASS.get(grid_char.lower())
    if klass is not None:
        return klass(grid, x, y, is_passive=grid_char.isupper())
    else:
        return None


def parse_grid(grid):
    operators = []
    for y, row in enumerate(grid.iter_rows()):
        for x, c in enumerate(row):
            if c != DOT_GLYPH:
                operator = operator_factory(grid, c, x, y)
                if operator is not None:
                    operators.append(operator)
                else:
                    logger.debug("No operator found for glyph %r", c)

    return operators


def update_grid(grid, frame):
    grid.reset_for_frame()

    operators = parse_grid(grid)
    logger.debug("Found %d operators", len(operators))

    for operator in operators:
        logger.debug(
            "Looking at operator %s, pos %d, %d", operator, operator.x, operator.y
        )
        if grid.is_locked(operator.x, operator.y):
            logger.debug(
                "Position @ %d, %d is locked (would be operator %s)",
                operator.x, operator.y, operator
            )
            continue
        operator.run(frame)


def render_grid(window, grid):
    for i, row in enumerate(grid.iter_rows()):
        window.move(i, 0)
        rendered_row = (c if c != DOT_GLYPH else EMPTY_GLYPH for c in row)
        window.addstr("".join(rendered_row))


def main(screen, path, use_midi):
    grid = OrcaGrid.from_path(path)
    if use_midi:
        from orca.midi import MidiIO, App
        print("Init midi...")
        midi_io = MidiIO()
        app = App(midi_io)
    else:
        class DummyApp:
            def push_note(self, *a, **kw):
                pass
            def run_midi(self):
                pass

    top_x = 20
    top_y = 5

    frame = 0

    # Must be called before any color setup
    curses.start_color()

    init_colors()

    # +1 as a hack to avoid ERR when writing on lower right corner
    window = curses.newwin(grid.rows, grid.cols + 1, top_y, top_x)
    window.keypad(True)

    def clear_window():
        for i in range(grid.rows):
            window.move(i, 0)
            window.addstr(" " * grid.cols)

    def render_top_banner():
        screen.addstr(0, 0, f"Frame: {frame}")

    clear_window()

    render_top_banner()
    screen.refresh()

    render_grid(window, grid)

    window.refresh()

    notes_index = (
        "C", "c", "D", "d", "E", "F", "f", "G", "g", "A", "a", "B"
    )

    while True:
        k = window.getch()
        if k == ord(" "):
            frame += 1
            logging.debug("Frame %r", frame)
            update_grid(grid, frame)
            for event in grid._midi_events:
                note = notes_index.index(event.note)
                note = event.octave * 12 + note + 24
                logger.debug("Playing on note %d", note)
                app.push_note(event.channel, note, event.velocity)

        app.run_midi()
        render_top_banner()
        screen.refresh()

        clear_window()
        render_grid(window, grid)

        window.refresh()


def main_cli(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("path", help="Path to .orca file.")
    p.add_argument("--use-midi", action="store_true")

    ns = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG, filename="curses-ui.log")
    screen = curses.initscr()

    try:
        # Do not echo typed keys into window
        with noecho():
            # Receive arrow keys, etc.
            with keypad(screen):
                # Hide cursor
                curses.curs_set(0)
                main(screen, ns.path, ns.use_midi)
                curses.napms(2000)
    finally:
        curses.endwin()


if __name__ == "__main__":
    main_cli()
