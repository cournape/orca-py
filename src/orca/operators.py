import abc
import logging
import math
import random

from orca.grid import BANG_GLYPH, COMMENT_GLYPH, DOT_GLYPH, MidiNoteOnEvent
from orca.ports import InputPort, OutputPort


logger = logging.getLogger(__name__)

OUTPUT_PORT_NAME = "output"


class IOperator(abc.ABC):
    def __init__(
        self, grid, x, y, name, description, *, glyph=DOT_GLYPH, is_passive=False
    ):
        self.x = x
        self.y = y

        self.name = name
        self.description = description

        self.ports = {}

        self._grid = grid

        self.is_passive = is_passive
        self.do_draw = is_passive

        self.glyph = glyph.upper() if is_passive else glyph

    @abc.abstractmethod
    def operation(self, frame, force=False):
        """Run the operator for the given frame and return the payload.

        This may modify the grid.

        Note: the frame is assumed to match the state of the grid given at
        construction time."""

    def __str__(self):
        return self.name

    def run(self, frame, force=False):
        payload = self.operation(frame, force)

        for port in self.ports.values():
            if isinstance(port, OutputPort) and port.is_bang:
                continue
            logger.debug(
                "Ops %s (%d, %d): locking port @ %d, %d",
                self.name,
                self.x,
                self.y,
                port.x,
                port.y,
            )
            self._grid.lock(port.x, port.y)

        output_port = self._output_port
        if output_port:
            if output_port.is_bang:
                self._bang(payload)
            else:
                self._output(payload)

    def erase(self):
        self._grid.poke(self.x, self.y, DOT_GLYPH)

    def explode(self):
        self._grid.poke(self.x, self.y, BANG_GLYPH)

    def has_neighbor(self, glyph):
        for x, y in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if self._grid.peek(self.x + x, self.y + y) == glyph:
                return True
        return False

    def move(self, offset_x, offset_y):
        new_x = self.x + offset_x
        new_y = self.y + offset_y
        if not self._grid.is_inside(new_x, new_y):
            self.explode()
            return

        collider = self._grid.peek(new_x, new_y)
        if collider not in (BANG_GLYPH, DOT_GLYPH):
            self.explode()
            return

        self.erase()
        self.x += offset_x
        self.y += offset_y
        self._grid.poke(self.x, self.y, self.glyph)
        if self._grid.is_inside(self.x, self.y):
            self._grid.lock(self.x, self.y)

    @property
    def _output_port(self):
        return self.ports.get(OUTPUT_PORT_NAME)

    def _has_output_port(self):
        return OUTPUT_PORT_NAME in self.ports

    def _should_upper_case(self):
        output_port = self._output_port
        if output_port is None or not output_port.is_sensitive:
            return False
        else:
            right_port = InputPort(self.x + 1, self.y)
            value = self._grid.listen(right_port)
            if value.lower() == value.upper() or value.upper() != value:
                return False
            else:
                return True

    def _bang(self, payload):
        output_port = self._output_port
        if output_port is None:
            logger.warn("Trying to bang, but no output port.")
            return
        else:
            glyph = BANG_GLYPH if payload else DOT_GLYPH
            self._grid.poke(output_port.x, output_port.y, glyph)

    def _output(self, glyph, port=None):
        if port is None:
            output_port = self._output_port
        else:
            output_port = port

        if output_port is None:
            logging.warn(
                "No output port for operator %s @ (%d, %d)", self.name, self.x, self.y
            )
        elif glyph is None:
            return
        else:
            if self._should_upper_case():
                value = glyph.upper()
            else:
                value = glyph
            self._grid.poke(output_port.x, output_port.y, value)


class Add(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid, x, y, "add", "Output sum of inputs", glyph="a", is_passive=is_passive
        )

        self.ports.update(
            {
                "a": InputPort(x - 1, y),
                "b": InputPort(x + 1, y),
                OUTPUT_PORT_NAME: OutputPort(x, y + 1, is_sensitive=True),
            }
        )

    def operation(self, frame, force=False):
        index = self._grid.listen_as_value(
            self.ports["a"]
        ) + self._grid.listen_as_value(self.ports["b"])
        return self._grid.key_of(index)


class Substract(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "substract",
            "Output difference of inputs",
            glyph="b",
            is_passive=is_passive,
        )

        self.ports.update(
            {
                "a": InputPort(x - 1, y),
                "b": InputPort(x + 1, y),
                OUTPUT_PORT_NAME: OutputPort(x, y + 1, is_sensitive=True),
            }
        )

    def operation(self, frame, force=False):
        a = self._grid.listen_as_value(self.ports["a"])
        b = self._grid.listen_as_value(self.ports["b"])
        return self._grid.key_of(abs(b - a))


class Clock(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "clock",
            "Outputs modulo of frame",
            glyph="c",
            is_passive=is_passive,
        )

        self.ports.update(
            {
                "rate": InputPort(x - 1, y, clamp=lambda x: max(1, x)),
                "mod": InputPort(x + 1, y, default="8"),
                OUTPUT_PORT_NAME: OutputPort(x, y + 1, is_sensitive=True),
            }
        )

    def operation(self, frame, force=False):
        rate = self._grid.listen_as_value(self.ports["rate"])
        mod = self._grid.listen_as_value(self.ports["mod"])

        value = math.floor(frame / rate) % mod
        return self._grid.key_of(value)


class Delay(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "delay",
            "Bangs on module of frame",
            glyph="d",
            is_passive=is_passive,
        )

        self.ports.update(
            {
                "rate": InputPort(x - 1, y, clamp=lambda x: max(1, x)),
                "mod": InputPort(x + 1, y, default="8"),
                OUTPUT_PORT_NAME: OutputPort(x, y + 1, is_bang=True),
            }
        )

    def operation(self, frame, force=False):
        rate = self._grid.listen_as_value(self.ports["rate"])
        mod = self._grid.listen_as_value(self.ports["mod"])

        value = frame % (mod * rate)
        return value == 0 or mod == 1


class East(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "east",
            "Move eastwards or bang",
            glyph="e",
            is_passive=is_passive,
        )
        self.do_draw = False

    def operation(self, frame, force=False):
        self.move(1, 0)
        self.is_passive = False


class Generator(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "generator",
            "Write operands with offset",
            glyph="g",
            is_passive=is_passive,
        )
        self.ports.update(
            {
                "x": InputPort(x - 3, y),
                "y": InputPort(x - 2, y),
                "len": InputPort(x - 1, y, clamp=lambda x: max(x, 1)),
            }
        )

    def operation(self, frame, force=False):
        length = self._grid.listen_as_value(self.ports["len"])
        x = self._grid.listen_as_value(self.ports["x"])
        y = self._grid.listen_as_value(self.ports["y"]) + 1

        for offset in range(length):
            input_port = InputPort(self.x + offset + 1, self.y)
            output_port = OutputPort(self.x + x + offset, self.y + y)
            self.ports.update(
                {
                    f"input{offset}": input_port,
                    f"output{offset}": output_port,
                }
            )
            res = self._grid.listen(input_port)
            self._output(res, output_port)


class Halt(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "half",
            "Halts southward operator",
            glyph="h",
            is_passive=is_passive,
        )

    def operation(self, frame, force=False):
        self._grid.lock(self.x, self.y + 1)  # self._output_port.x, self._output_port.y)


class If(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "if",
            "Bang if inputs are equal",
            glyph="f",
            is_passive=is_passive,
        )

        self.ports.update(
            {
                "a": InputPort(x - 1, y),
                "b": InputPort(x + 1, y),
                OUTPUT_PORT_NAME: OutputPort(x, y + 1, is_bang=True),
            }
        )

    def operation(self, frame, force=False):
        a = self._grid.listen(self.ports["a"])
        b = self._grid.listen(self.ports["b"])
        return a == b


class Increment(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "increment",
            "Increment operator southward",
            glyph="i",
            is_passive=is_passive,
        )
        self.ports.update(
            {
                "step": InputPort(x - 1, y, default="1"),
                "mod": InputPort(x + 1, y),
                OUTPUT_PORT_NAME: OutputPort(x, y + 1, is_sensitive=True),
            }
        )

    def operation(self, frame, force=False):
        step = self._grid.listen_as_value(self.ports["step"])
        mod = self._grid.listen_as_value(self.ports["mod"])
        out = self._grid.listen_as_value(self.ports[OUTPUT_PORT_NAME])
        return self._grid.key_of((out + step) % (mod if mod > 0 else 36))


class Jumper(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "j",
            "Outputs northward operator",
            glyph="f",
            is_passive=is_passive,
        )

        self.ports.update(
            {
                "val": InputPort(x, y - 1),
                OUTPUT_PORT_NAME: OutputPort(x, y + 1),
            }
        )

    def operation(self, frame, force=False):
        self._grid.lock(self._output_port.x, self._output_port.y)
        return self._grid.listen(self.ports["val"])


class Multiply(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "multiply",
            "Output multiplication of inputs",
            glyph="m",
            is_passive=is_passive,
        )

        self.ports.update(
            {
                "a": InputPort(x - 1, y),
                "b": InputPort(x + 1, y),
                OUTPUT_PORT_NAME: OutputPort(x, y + 1, is_sensitive=True),
            }
        )

    def operation(self, frame, force=False):
        a = self._grid.listen_as_value(self.ports["a"])
        b = self._grid.listen_as_value(self.ports["b"])
        return self._grid.key_of(a * b)


class North(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "north",
            "Move northward or bang",
            glyph="n",
            is_passive=is_passive,
        )
        self.do_draw = False

    def operation(self, frame, force=False):
        self.move(0, -1)
        self.is_passive = False


class Random(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "random",
            "Outputs random value",
            glyph="r",
            is_passive=is_passive,
        )

        self.ports.update(
            {
                "min": InputPort(x - 1, y),
                "max": InputPort(x + 1, y),
                OUTPUT_PORT_NAME: OutputPort(x, y + 1, is_sensitive=True),
            }
        )

    def operation(self, frame, force=False):
        low = self._grid.listen_as_value(self.ports["min"])
        high = self._grid.listen_as_value(self.ports["max"])

        value = random.randint(low, high)
        return self._grid.key_of(value)


class South(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "south",
            "Move southward or bang",
            glyph="s",
            is_passive=is_passive,
        )
        self.do_draw = False

    def operation(self, frame, force=False):
        self.move(0, 1)
        self.is_passive = False


class Track(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "track",
            "Reads eastward operand",
            glyph="t",
            is_passive=is_passive,
        )
        self.ports.update(
            {
                "key": InputPort(x - 2, y),
                "len": InputPort(x - 1, y, clamp=lambda x: max(1, x)),
                OUTPUT_PORT_NAME: OutputPort(x, y + 1),
            }
        )

    def operation(self, frame, force=False):
        key = self._grid.listen_as_value(self.ports["key"])
        length = self._grid.listen_as_value(self.ports["len"])

        for offset in range(length):
            self._grid.lock(self.x + offset + 1, self.y)

        port = InputPort(self.x + 1 + key % length, self.y)
        return self._grid.listen(port)


class West(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "west",
            "Move westward or bang",
            glyph="w",
            is_passive=is_passive,
        )
        self.do_draw = False

    def operation(self, frame, force=False):
        self.move(-1, 0)
        self.is_passive = False


class Bang(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "bang",
            "Bangs neighboring operands",
            glyph=BANG_GLYPH,
            is_passive=is_passive,
        )
        self.do_draw = False

    def operation(self, frame, force=False):
        self.do_draw = False
        self.erase()


class Comment(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "comment",
            "Halts line",
            glyph=COMMENT_GLYPH,
            is_passive=is_passive,
        )
        self.do_draw = False

    def operation(self, frame, force=False):
        self._grid.lock(self.x, self.y)
        for x in range(self.x + 1, self._grid.cols):
            self._grid.lock(x, self.y)
            if self._grid.peek(x, self.y) == self.glyph:
                break


_NOTES_VALUES = ("C", "c", "D", "d", "E", "F", "f", "G", "g", "A", "a", "B")
NOTE_TO_INDEX = {k: i for i, k in enumerate(_NOTES_VALUES)}


class Midi(IOperator):
    def __init__(self, grid, x, y, *, is_passive=False):
        super().__init__(
            grid,
            x,
            y,
            "midi",
            "Send MIDI note",
            glyph=":",
            is_passive=True,
        )

        self.ports.update(
            {
                "channel": InputPort(self.x + 1, self.y),
                "octave": InputPort(
                    self.x + 2, self.y, clamp=lambda x: min(max(0, x), 8)
                ),
                "note": InputPort(self.x + 3, self.y),
                "velocity": InputPort(
                    self.x + 4, self.y, default="f", clamp=lambda x: min(max(0, x), 16)
                ),
                "length": InputPort(
                    self.x + 5, self.y, clamp=lambda x: min(max(0, x), 32)
                ),
            }
        )

    def operation(self, frame, force=False):
        if not self.has_neighbor(BANG_GLYPH) and not force:
            return

        for port_name in "channel", "octave", "note":
            if self._grid.listen(self.ports[port_name]) == DOT_GLYPH:
                return

        note = self._grid.listen(self.ports["note"])
        if not NOTE_TO_INDEX:
            return

        channel = self._grid.listen_as_value(self.ports["channel"])
        if channel > 15:
            return
        octave = self._grid.listen_as_value(self.ports["octave"])
        velocity = self._grid.listen_as_value(self.ports["velocity"])
        length = self._grid.listen_as_value(self.ports["length"])

        self._grid.push_midi(MidiNoteOnEvent(channel, octave, note, velocity, length))
