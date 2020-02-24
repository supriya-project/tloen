from functools import singledispatchmethod

from prompt_toolkit import layout, widgets, application

from ..events import (
    ApplicationBooted,
    ApplicationBooting,
    ApplicationQuit,
    ApplicationQuitting,
    ApplicationStatusRefreshed,
)
from ..pubsub import PubSub


class StatusWidget:
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
            "port": ".....",
            "sample_rate": "sr: ...... /   0.000%",
            "status": "offline",
            "synthdefs": "d: ....",
            "synths": "s: ....",
            "ugens": "u: .....",
        }
        self.text = self.text_defaults.copy()
        split = layout.VSplit(
            [
                widgets.Box(layout.Window(control), padding_left=1, padding_right=1)
                for control in
                [
                    layout.FormattedTextControl(lambda: self.text["status"].ljust(8)),
                    layout.FormattedTextControl(lambda: self.text["port"].ljust(5)),
                    layout.FormattedTextControl(lambda: self.text["cpu"]),
                    layout.FormattedTextControl(lambda: self.text["sample_rate"]),
                    layout.FormattedTextControl(lambda: self.text["ugens"]),
                    layout.FormattedTextControl(lambda: self.text["groups"]),
                    layout.FormattedTextControl(lambda: self.text["synths"]),
                    layout.FormattedTextControl(lambda: self.text["synthdefs"]),
                ]
            ],
            padding=1,
            padding_char="|",
        )
        self.container = widgets.Frame(
            widgets.Box(split), height=3, title="server status",
        )

    @singledispatchmethod
    def handle_event(self, event):
        ...

    @handle_event.register
    def _handle_application_booted(self, event: ApplicationBooted):
        self.text["status"] = "booted "
        self.text["port"] = str(event.port)
        application.get_app()._redraw()

    @handle_event.register
    def _handle_application_booting(self, event: ApplicationBooting):
        self.text["status"] = "booting"
        application.get_app().invalidate()

    @handle_event.register
    def _handle_application_quit(self, event: ApplicationQuit):
        self.text.update(self.text_defaults)
        application.get_app().invalidate()

    @handle_event.register
    def _handle_application_quitting(self, event: ApplicationQuitting):
        self.text["status"] = "quitting"
        application.get_app().invalidate()

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
        application.get_app().invalidate()

    def __pt_container__(self):
        return self.container
