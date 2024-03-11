import dataclasses

from supriya.clocks import Moment

from ..bases import Event


@dataclasses.dataclass
class TransportStarted(Event):
    pass


@dataclasses.dataclass
class TransportStopped(Event):
    pass


@dataclasses.dataclass
class TransportTicked(Event):  # TODO: ClipView needs to know start delta
    moment: Moment
