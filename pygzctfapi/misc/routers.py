from typing import List
from pygzctfapi.misc.events import BaseEventsClass, Event, NoticeTrackerEvents
from pygzctfapi import exceptions
import threading


class BaseRouter:
    events: BaseEventsClass
    
    def __init__(self):
        self._handlers = {k: list() for k in self.events}
        self._lock = threading.Lock()
    
    def handle(self, event: str) -> callable:
        """
        Decorator to register a handler for an event.

        Args:
            event (str): The event to listen to, can be fetched from router.events

        Returns:
            callable: A decorator function to register a handler.
        """
        
        def decorator(handler: callable) -> callable:
            self.add_handler(event, handler)
            return handler
        return decorator

    def add_handler(self, event_name: str, handler: callable, raise_on_exist: bool = True):
        """
        Add a handler for an event to the router.

        Args:
            event_name (str): The event name to listen to, can be fetched from router.events
            handler (callable): The handler to add
            raise_on_exist (bool): Whether to raise an exception if the handler is already registered. Defaults to True.

        Raises:
            HandlerAlreadyRegisteredError: When raise_on_exist is True and the handler is already registered.
            EventTypeError: When the event_type is not valid.
        """
        with self._lock:
            if event_name in self.events:
                if handler not in self._handlers[event_name]:
                    self._handlers[event_name].append(handler)
                elif raise_on_exist:
                    raise exceptions.HandlerAlreadyRegisteredError(handler=handler)
            else:
                raise exceptions.EventTypeError(event_type=event_name, dispatcher=self)
    
    def remove_handler(self, event_name: str, handler: callable, raise_on_not_exist: bool = True):
        """
        Remove a handler for an event from the router.

        Args:
            event_name (str): The event name to remove the handler from, can be fetched from router.events
            handler (callable): The handler to remove
            raise_on_not_exist (bool): Whether to raise an exception if the handler is not registered. Defaults to True.

        Raises:
            HandlerNotRegisteredError: When raise_on_not_exist is True and the handler is not registered.
            EventTypeError: When the event_type is not valid.
        """
        with self._lock:
            if event_name in self.events:
                if handler in self._handlers[event_name]:
                    self._handlers[event_name].remove(handler)
                elif raise_on_not_exist:
                    raise exceptions.HandlerNotRegisteredError(handler=handler)
            else:
                raise exceptions.EventTypeError(event_type=event_name, router=self)
    
    def clear_handlers(self, event_type: str):
        """
        Clear all handlers for a specific event type.

        Args:
            event_type (str): The event name to clear the handlers for, can be fetched from router.events

        Raises:
            EventTypeError: When the event_type is not valid.
        """
        with self._lock:
            if event_type in self.events:
                self._handlers[event_type].clear()
            else:
                raise exceptions.EventTypeError(event_type=event_type, router=self)
    
    def get_handlers(self, event_type: str) -> List[callable]:
        """
        Get all handlers for a specific event type.

        Args:
            event_type (str): The event name to get the handlers for, can be fetched from router.events

        Returns:
            list: A list of handlers for the given event type

        Raises:
            EventTypeError: When the event_type is not valid.
        """
        with self._lock:
            if event_type in self.events:
                return self._handlers[event_type]
            else:
                raise exceptions.EventTypeError(event_type=event_type, router=self)
    
    def trigger_event(self, event: Event):
        """
        Recieve an event and trigger the handlers for it.

        Args:
            event (Event): The event to trigger the handlers for

        Raises:
            EventTypeError: When the event type is not valid.
        """
        with self._lock:
            if event.event in self._handlers:
                for handler in self._handlers[event.event]:
                    handler(event.data)
                if hasattr(self.events, 'any') and self.events.any in self._handlers:
                    for handler in self._handlers[self.events.any]:
                        handler(event.data)
            # else:
            #     raise exceptions.EventTypeError(event_type=event.event, router=self)


class NoticeTrackerRouter(BaseRouter):
    events: NoticeTrackerEvents
    def __init__(self):
        self.events = NoticeTrackerEvents()
        super().__init__()
        
    