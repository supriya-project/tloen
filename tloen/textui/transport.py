try:
    from functools import singledispatchmethod
except ImportError:
    from singledispatchmethod import singledispatchmethod

from prompt_toolkit import layout, widgets, application

from ..events import (
    TransportStarted,
    TransportStopped,
    TransportTicked,
)
from ..pubsub import PubSub


class TransportWidget:
    def __init__(self, pubsub=None):
        self.pubsub = pubsub or PubSub()
        self.pubsub.subscribe(
            self.handle_event,
            TransportStarted,
            TransportStopped,
            TransportTicked,
        )
        self.text = {
            "status": "stopped",
            "tempo": "120.0 bpm",
            "time_signature": " 4 /  4",
            "tick": "1.1.1",
        }
        self.container = widgets.Frame(
            layout.Window(
                layout.FormattedTextControl(
                    lambda: " | ".join([
                        self.text["status"],
                        self.text["tempo"],
                        self.text["time_signature"],
                        self.text["tick"],
                    ])
                ),
                height=1,
                ignore_content_height=True,
            ),
            height=3,
            title="transport",
        )

    @singledispatchmethod
    def handle_event(self, event):
        ...

    @handle_event.register
    def _on_transport_started(self, event: TransportStarted):
        self.text["status"] = "running"
        application.get_app().invalidate()

    @handle_event.register
    def _on_transport_stopped(self, event: TransportStopped):
        self.text["status"] = "stopped"
        application.get_app().invalidate()

    @handle_event.register
    def _on_transport_ticked(self, event: TransportTicked):
        self.text["tempo"] = "{:5.1f} bpm".format(event.moment.beats_per_minute)
        self.text["time_signature"] = "{:2d} / {:2d}".format(*event.moment.time_signature)
        denominator = event.moment.time_signature[1]
        measure = event.moment.measure
        measure_offset = event.moment.measure_offset
        beat, beat_offset = divmod(measure_offset, 1 / denominator)
        tick = beat_offset / (1 / denominator) * 4
        self.text["tick"] = "{} / {} / {}".format(measure, int(beat + 1), int(tick + 1))
        application.get_app().invalidate()

    def __pt_container__(self):
        return self.container
