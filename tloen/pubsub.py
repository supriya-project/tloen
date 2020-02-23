from typing import Callable, Dict, List, Type

from .events import Event


class PubSub:
    def __init__(self):
        self.subscriptions: Dict[Type[Event], List[Callable[Event]]] = {}

    def publish(self, event: Event):
        callables = self.subscriptions.get(type(event), [])
        # raise RuntimeError("THE FUCK", event, callables)
        for procedure in callables:
            procedure(event)

    def subscribe(self, procedure: Callable, *event_classes: Type[Event]):
        for event_class in event_classes:
            self.subscriptions.setdefault(event_class, []).append(procedure)

    def unsubscribe(self, procedure: Callable, *event_classes: Type[Event]):
        for event_class in event_classes:
            callables = self.subscriptions.get(event_class, [])
            callables.remove(procedure)
            if not callables:
                self.subscriptions.pop(event_class, None)
