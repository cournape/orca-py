def default_clamp(v):
    return v


# Ports represent input/output on the grid. Port instances encompass some of
# the details about how to interpret the given value in the grid.
class IPort:
    def __init__(self, x, y, *, clamp=None, default=None):
        self.x = x
        self.y = y

        self.clamp = clamp or default_clamp
        self.default = default


class InputPort(IPort):
    pass


class OutputPort(IPort):
    def __init__(
        self, x, y, *, clamp=None, default=None, is_sensitive=False, is_bang=False
    ):
        super().__init__(x, y, clamp=clamp, default=default)

        self.is_sensitive = is_sensitive
        self.is_bang = is_bang
