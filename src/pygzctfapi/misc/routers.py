from enum import StrEnum
from typing import List
from pygzctfapi import exceptions
import threading


class Router:
    event_enums: List[StrEnum]
    
    def __init__(self, *event_enums: StrEnum):
        """
        Initialize a Router.

        The Router is used to route events to handlers.
        The given event_enums are used to define the events that can be handled by the router.
        The router keeps track of the handlers registered for each event.
        It also keeps track of a lock to ensure thread safety.

        Parameters
        ----------
        event_enums: List[StrEnum]
            The event enums that define the events that can be handled by the router.

        Raises
        ------
        EventsIntersectionError
            If any of the given event enums intersect with the existing events in the router.
        """
        self.event_enums = list(event_enums)
        self._handlers : dict[str, List[callable]] = {}
        for enum in event_enums:
            intersection = set(enum) & set(self._handlers.keys())
            if intersection:
                raise exceptions.EventsIntersectionError(intersection=intersection, router=self)
            self._handlers.update({k: list() for k in enum})
        self._lock = threading.Lock()
    
    def add_event_enums(self, *event_enums: StrEnum, raise_on_exist: bool = True):
        """
        Add one or more event enums to the router.
        
        The given event enums are added to the router, and the routing for the events in the enums are initialized.

        Parameters
        ----------
        *event_enums: List[StrEnum]
            The event enums to add to the router.
        raise_on_exist: bool
            Whether to raise an exception if any of the given event enums already exist in the router.
            Defaults to True.

        Raises
        ------
        EventsIntersectionError
            If any of the given event enums intersect with the existing events in the router.
        EventEnumExistsError
            If any of the given event enums already exist in the router and raise_on_exist is True.
        """
        for enum in event_enums:
            if enum not in self.event_enums:
                intersection = set(enum) & set(self._handlers.keys())
                if intersection:
                    raise exceptions.EventsIntersectionError(intersection=intersection, router=self)
                self.event_enums.append(enum)
                self._handlers.update({k: list() for k in enum})
            elif raise_on_exist:
                raise exceptions.EventEnumExistsError(enum=enum, router=self)
    
    def remove_event_enums(self, *event_enums: StrEnum, raise_on_not_exist: bool = True):
        """
        Remove one or more event enums from the router.
        
        The given event enums are removed from the router, and the routing for the events in the enums are removed.
        After that, you will not able to register handlers for the events from that enums.

        Parameters
        ----------
        *event_enums: List[StrEnum]
            The event enums to remove from the router.
        raise_on_not_exist: bool
            Whether to raise an exception if any of the given event enums do not exist in the router.
            Defaults to True.

        Raises
        ------
        EventEnumNotExistsError
            If any of the given event enums do not exist in the router and raise_on_not_exist is True.
        """
        for enum in event_enums:
            if enum in self.event_enums:
                self.event_enums.remove(enum)
                for event in enum:
                    self._handlers.pop(event)
            elif raise_on_not_exist:
                raise exceptions.EventEnumNotExistsError(enum=enum, router=self)
    
    def handle(self, *events: str, raise_on_exist: bool = True) -> callable:
        """
        Decorator to register a handler for an events.

        Args:
            *events (str): The events that should be routed to the handler.
            raise_on_exist (bool): Whether to raise an exception if the handler is already registered. Defaults to True.

        Returns:
            callable: A decorator function to register a handler.
        """
        
        def decorator(handler: callable) -> callable:
            self.add_handler(handler, *events, raise_on_exist=raise_on_exist)
            return handler
        return decorator

    def add_handler(self, handler: callable, *events: str, raise_on_exist: bool = True):
        """
        Add a handler for desired events to the router.

        Args:
            handler (callable): The handler to add
            *events (str): The events that should be routed to the handler.
            raise_on_exist (bool): Whether to raise an exception if the handler is already registered. Defaults to True.

        Raises:
            HandlerAlreadyRegisteredError: When raise_on_exist is True and the handler is already registered.
            EventNotExistsError: When the event does not exist in this router.
        """
        with self._lock:
            for event in events:
                if event in self._handlers:
                    if handler not in self._handlers[event]:
                        self._handlers[event].append(handler)
                    elif raise_on_exist:
                        raise exceptions.HandlerAlreadyRegisteredError(handler=handler)
                else:
                    raise exceptions.EventNotExistsError(event=event, router=self)
    
    def remove_handler(self, handler: callable, *events: str, raise_on_not_exist: bool = True):
        """
        Remove a handler for desired events from the router.

        Args:
            handler (callable): The handler to remove
            *events (str): The events to remove the routing for that handler.
            raise_on_not_exist (bool): Whether to raise an exception if the handler is not registered. Defaults to True.

        Raises:
            HandlerNotRegisteredError: When raise_on_not_exist is True and the handler is not registered.
            EventNotExistsError: When the event does not exist in this router.
        """
        with self._lock:
            for event in events:
                if event in self._handlers:
                    if handler in self._handlers[event]:
                        self._handlers[event].remove(handler)
                    elif raise_on_not_exist:
                        raise exceptions.HandlerNotRegisteredError(handler=handler)
                else:
                    raise exceptions.EventNotExistsError(event=event, router=self)
    
    def clear_handlers(self, *events: str):
        """
        Clear all handlers for a specific events.

        Args:
            *events (str): The events to clear the handlers for

        Raises:
            EventNotExistsError: When the event does not exist in this router.
        """
        with self._lock:
            for event in events:
                if event in self._handlers:
                    self._handlers[event].clear()
                else:
                    raise exceptions.EventNotExistsError(event=event, router=self)
    
    def get_handlers(self, *events: str) -> List[callable]:
        """
        Get all handlers for a specific events.

        Args:
            *events (str): The events to retrieve the handlers for

        Returns:
            list: A list of handlers for the given events

        Raises:
            EventNotExistsError: When the event does not exist in this router.
        """
        with self._lock:
            handlers = []
            for event in events:
                if event in self._handlers:
                    handlers.extend(self._handlers[event])
                else:
                    raise exceptions.EventNotExistsError(event=event, router=self)
            return handlers
    
    def trigger_event(self, event: str, *args, **kwargs):
        """
        Recieve an event and trigger the handlers for it.

        Args:
            event (str): The event to trigger the handlers for
            *args: The arguments to pass to the handlers
            **kwargs: The keyword arguments to pass to the handlers

        Raises:
            EventNotExistsError: When the event does not exist in this router.
        """
        with self._lock:
            if event in self._handlers:
                for handler in self._handlers[event]:
                    handler(event, *args, **kwargs)
            else:
                raise exceptions.EventNotExistsError(event=event, router=self)
        
    