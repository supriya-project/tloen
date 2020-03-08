from functools import singledispatchmethod

import urwid

from ..domain.applications import (
    ApplicationBooted,
    ApplicationBooting,
    ApplicationQuit,
    ApplicationQuitting,
    ApplicationStatusRefreshed,
)
from ..pubsub import PubSub


class StatusWidget(urwid.WidgetWrap):
    def __init__(self, pubsub=None):
        self.pubsub = pubsub or PubSub()
        self.pubsub.subscribe(
            self.handle_event,
            ApplicationBooted,
            ApplicationBooting,
            ApplicationQuit,
            ApplicationQuitting,
            ApplicationStatusRefreshed,
        )
        self.text_defaults = {
            "cpu": "cpu:   0.00% /   0.00%",
            "groups": "g: ....",
            "port": ".....".ljust(5),
            "sample_rate": "sr: ...... /   0.000%",
            "status": "offline".ljust(8),
            "synthdefs": "d: ....",
            "synths": "s: ....",
            "ugens": "u: .....",
        }
        self.text = self.text_defaults.copy()
        self.text_widget = urwid.Text(self.build_text())
        self._w = urwid.LineBox(
            urwid.Padding(self.text_widget, left=1, right=1, width="pack",),
            title="server status",
            title_align="right",
        )

    def build_text(self):
        return " | ".join(
            [
                self.text["status"],
                self.text["port"],
                self.text["cpu"],
                self.text["sample_rate"],
                self.text["groups"],
                self.text["synths"],
                self.text["synthdefs"],
                self.text["ugens"],
            ]
        )

    def update_text(self):
        self.text_widget.set_text(self.build_text())

    @singledispatchmethod
    def handle_event(self, event):
        ...

    @handle_event.register
    def _handle_application_booted(self, event: ApplicationBooted):
        self.text["status"] = "online".ljust(8)
        self.text["port"] = str(event.port).ljust(5)
        self.update_text()

    @handle_event.register
    def _handle_application_booting(self, event: ApplicationBooting):
        self.text["status"] = "booting".ljust(8)
        self.update_text()

    @handle_event.register
    def _handle_application_quit(self, event: ApplicationQuit):
        self.text.update(self.text_defaults)
        self.update_text()

    @handle_event.register
    def _handle_application_quitting(self, event: ApplicationQuitting):
        self.text["status"] = "quitting".ljust(8)
        self.update_text()

    @handle_event.register
    def _handle_application_status_refreshed(self, event: ApplicationStatusRefreshed):
        self.text["cpu"] = "cpu: {:6.2f}% / {:6.2f}%".format(
            event.status.average_cpu_usage, event.status.peak_cpu_usage
        )
        self.text["groups"] = "g: {:4d}".format(event.status.group_count)
        self.text["synthdefs"] = "d: {:4d}".format(event.status.synthdef_count)
        self.text["synths"] = "s: {:4d}".format(event.status.synth_count)
        self.text["ugens"] = "u: {:5d}".format(event.status.ugen_count)

        self.text["sample_rate"] = "sr: {:6d} / {:7.3f}%".format(
            int(event.status.target_sample_rate),
            (event.status.actual_sample_rate / event.status.target_sample_rate) * 100,
        )
        self.update_text()
