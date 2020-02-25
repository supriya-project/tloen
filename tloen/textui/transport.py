from functools import singledispatchmethod

import urwid

from ..events import TransportStarted, TransportStopped, TransportTicked
from ..pubsub import PubSub


class TransportWidget(urwid.WidgetWrap):
    def __init__(self, pubsub=None):
        self.pubsub = pubsub or PubSub()
        self.pubsub.subscribe(
            self.handle_event, TransportStarted, TransportStopped, TransportTicked,
        )
        self.text = {
            "status": "stopped",
            "tempo": "120.0 bpm",
            "time_signature": " 4 /  4",
            "tick": "1 / 1 / 1",
        }
        self.text_widget = urwid.Text(self.build_text())
        self._w = urwid.LineBox(
            urwid.Padding(
                self.text_widget,
                left=1,
                right=1,
                width="pack",
            ),
            title="transport",
            title_align="left",
        )

    def build_text(self):
        return " | ".join(
            [
                self.text["status"],
                self.text["tempo"],
                self.text["time_signature"],
                self.text["tick"],
            ]
        )

    def update_text(self):
        self.text_widget.set_text(self.build_text())

    @singledispatchmethod
    def handle_event(self, event):
        ...

    @handle_event.register
    def _on_transport_started(self, event: TransportStarted):
        self.text["status"] = "running"
        self.update_text()

    @handle_event.register
    def _on_transport_stopped(self, event: TransportStopped):
        self.text["status"] = "stopped"
        self.update_text()

    @handle_event.register
    def _on_transport_ticked(self, event: TransportTicked):
        self.text["tempo"] = "{:5.1f} bpm".format(event.moment.beats_per_minute)
        self.text["time_signature"] = "{:2d} / {:2d}".format(
            *event.moment.time_signature
        )
        denominator = event.moment.time_signature[1]
        measure = event.moment.measure
        measure_offset = event.moment.measure_offset
        beat, beat_offset = divmod(measure_offset, 1 / denominator)
        tick = beat_offset / (1 / denominator) * 4
        self.text["tick"] = "{} / {} / {}".format(measure, int(beat + 1), int(tick + 1))
        self.update_text()
