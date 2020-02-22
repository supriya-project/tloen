from typing import Callable, Dict, List, Type

from .events import Event


subscriptions = {}


class PubSub:

    def __init__(self):
        self.subscriptions: Dict[Type[Event], List[Callable[Event]]] = {}

    def publish(event: Event):
        for procedure in subscriptions.get(type(event), []):
            procedure(event)

    def subscribe(self, event_class: Type[Event], procedure: callable):
        subscriptions.setdfault(event_class, []).append(procedure)

    def unsubscribe(self, event_class: Type[Event], procedure: callable):
        subscriptions.get(event_class, []).remove(procedure)
