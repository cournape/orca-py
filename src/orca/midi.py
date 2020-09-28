import rtmidi


class MidiIO:
    def __init__(self):
        midiout = rtmidi.MidiOut()
        available_ports = midiout.get_ports()
        if available_ports:
            midiout.open_port(0)
            self._midiout = midiout
        else:
            raise ValueError("No port available")

    def send_message(self, msg):
        self._midiout.send_message(msg)


class App:
    def __init__(self, midi_io):
        self.midi_io = midi_io

        self._stack = set()
        self._stack_off = set()

    def push_note(self, channel, note, velocity):
        self._stack.add((channel, note, velocity))

    def run_midi(self):
        for channel, note, velocity in self._stack_off:
            self.midi_io.send_message([0x80 + channel, note, velocity])
        self._stack_off = set()

        for channel, note, velocity in self._stack:
            self.midi_io.send_message([0x90 + channel, note, velocity])
            self._stack_off.add((channel, note, velocity))
        self._stack = set()


if __name__ == "__main__":
    midi_io = MidiIO()
    app = App(midi_io)
    print("App started")

    def triade(k, velocity):
        for i in range(3):
            app.push_note(0, k + i * 5, velocity)

    triade(61, 119)
    app.run_midi()
