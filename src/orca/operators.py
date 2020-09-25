import abc
import logging
import math

from orca.grid import BANG_GLYPH, DOT_GLYPH
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

        This does not modify the grid.

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
                "Ops %d, %d: locking port @ %d, %d", self.x, self.y, port.x, port.y
            )
            self._grid.lock(port.x, port.y)

        output_port = self._output_port
        if output_port:
            if output_port.is_bang:
                raise ValueError("Output bang not implemented yet")
            else:
                self._output(payload)

    def erase(self):
        self._grid.poke(self.x, self.y, DOT_GLYPH)

    def explode(self):
        self._grid.poke(self.x, self.y, BANG_GLYPH)

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
        if output_port is None or output_port.is_sensitive:
            return False
        else:
            right_port = InputPort(self.x + 1, self.y)
            value = self._grid.listen(right_port)
            if value.lower() == value.upper() or value.upper() == value:
                return False
            else:
                return True

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
            self.ports.update({
                f"input{offset}": input_port,
                f"output{offset}": output_port,
            })
            res = self._grid.listen(input_port)
            self._output(res, output_port)


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
