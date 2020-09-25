import abc
import logging
import math

from orca.grid import DOT_GLYPH
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

    def _output(self, glyph):
        output_port = self._output_port
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
