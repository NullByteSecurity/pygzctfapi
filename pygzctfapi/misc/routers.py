from pygzctfapi.misc.events import BaseEventsClass, Event, NoticeTrackerEvents
from pygzctfapi import exceptions
import threading


def handler_decorator_factory(event_type: str, router: 'BaseRouter'):
    """
    Returns a decorator that can be used to register a handler for a given event_type.
    
    The returned decorator will register the given handler with the router.
    
    Parameters
    ----------
    event_type : str
        The type of event to register the handler for.
    """
    def decorator(handler: callable):
        """
        Decorator that registers a handler with the router.
        
        The handler will be called by the router when an event of the type specified by `event_type` is triggered.
        
        Parameters
        ----------
        handler : callable
            The handler to register. This should be a callable that takes in the same number of arguments as the event_type.
        """
        router._handlers[event_type].append(handler)
        return handler
    return decorator

class BaseRegistrator:
    pass

class BaseRouter:
    events: BaseEventsClass
    registrator: BaseRegistrator
    
    def __init__(self):
        self._handlers = {k: list() for k in self.events}
        self._lock = threading.Lock()

    def add_handler(self, event_type: str, handler: callable, raise_on_exist: bool = True):
        with self._lock:
            if event_type in self.events:
                if handler not in self._handlers[event_type]:
                    self._handlers[event_type].append(handler)
                elif raise_on_exist:
                    raise exceptions.HandlerAlreadyRegisteredError(handler=handler)
            else:
                raise exceptions.EventTypeError(event_type=event_type, dispatcher=self)
    
    def remove_handler(self, event_type: str, handler: callable, raise_on_not_exist: bool = True):
        with self._lock:
            if event_type in self.events:
                if handler in self._handlers[event_type]:
                    self._handlers[event_type].remove(handler)
                elif raise_on_not_exist:
                    raise exceptions.HandlerNotRegisteredError(handler=handler)
            else:
                raise exceptions.EventTypeError(event_type=event_type, router=self)
    
    def clear_handlers(self, event_type: str):
        with self._lock:
            if event_type in self.events:
                self._handlers[event_type].clear()
            else:
                raise exceptions.EventTypeError(event_type=event_type, router=self)
    
    def get_handlers(self, event_type: str):
        with self._lock:
            if event_type in self.events:
                return self._handlers[event_type]
            else:
                raise exceptions.EventTypeError(event_type=event_type, router=self)
    
    def trigger_event(self, event: Event):
        with self._lock:
            if event.event in self._handlers:
                for handler in self._handlers[event.event]:
                    handler(event.data)
                if hasattr(self.events, 'any') and self.events.any in self._handlers:
                    for handler in self._handlers[self.events.any]:
                        handler(event.data)
            # else:
            #     raise exceptions.EventTypeError(event_type=event.event, router=self)

class _NoticeTrackerRegistrator(BaseRegistrator):
    new: callable
    edited: callable
    deleted: callable
    any: callable

class NoticeTrackerRouter(BaseRouter):
    events: NoticeTrackerEvents
    registrator: _NoticeTrackerRegistrator
    def __init__(self):
        self.events = NoticeTrackerEvents()
        self.registrator = _NoticeTrackerRegistrator()
        self.registrator.new = staticmethod(handler_decorator_factory(self.events.new, self))
        self.registrator.edited = staticmethod(handler_decorator_factory(self.events.edited, self))
        self.registrator.deleted = staticmethod(handler_decorator_factory(self.events.deleted, self))
        self.registrator.any = staticmethod(handler_decorator_factory(self.events.any, self))
        super().__init__()
        
    