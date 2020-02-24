try:
    from functools import singledispatchmethod
except ImportError:
    from singledispatchmethod import singledispatchmethod

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
            "port": ".....".ljust(5),
            "sample_rate": "sr: ...... /   0.000%",
            "status": "offline".ljust(8),
            "synthdefs": "d: ....",
            "synths": "s: ....",
            "ugens": "u: .....",
        }
        self.text = self.text_defaults.copy()
        self.container = widgets.Frame(
            layout.Window(
                layout.FormattedTextControl(
                    lambda: " | ".join([
                        self.text["status"],
                        self.text["port"],
                        self.text["cpu"],
                        self.text["sample_rate"],
                        self.text["groups"],
                        self.text["synths"],
                        self.text["synthdefs"],
                        self.text["ugens"],
                    ]),
                ),
                height=1,
                ignore_content_height=True,
            ),
            height=3,
            title="server status",
        )

    @singledispatchmethod
    def handle_event(self, event):
        ...

    @handle_event.register
    def _handle_application_booted(self, event: ApplicationBooted):
        self.text["status"] = "booted".ljust(8)
        self.text["port"] = str(event.port).ljust(5)
        application.get_app().invalidate()

    @handle_event.register
    def _handle_application_booting(self, event: ApplicationBooting):
        self.text["status"] = "booting".ljust(8)
        application.get_app().invalidate()

    @handle_event.register
    def _handle_application_quit(self, event: ApplicationQuit):
        self.text.update(self.text_defaults)
        application.get_app().invalidate()

    @handle_event.register
    def _handle_application_quitting(self, event: ApplicationQuitting):
        self.text["status"] = "quitting".ljust(8)
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
