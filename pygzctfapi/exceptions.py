from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygzctfapi.misc.trackers import DispatchableTracker
    from pygzctfapi.misc.routers import BaseRouter


class Raiser:
    @staticmethod
    def raise_for_status(response):
        if response.status_code != 200:
            if response.headers.get('Content-Type') == 'application/json':
                msg = response.json()
                if 'title' in msg:
                    raise RequestFailedError(status_code=response.status_code, reason=msg['title'])
                else:
                    raise RequestFailedError(status_code=response.status_code, reason=msg)
            raise RequestFailedError(status_code=response.status_code, reason=response.text)

class GZException(Exception):
    """Base class for exceptions raised by pygzctfapi."""
    pass

class NotAuthorizedError(GZException):
    """Raised when a method is called without authorization."""
    
    def __init__(self, message="You are not allowed to perform this action."):
        self.message = message
        super().__init__(self.message)

class AuthenticationError(GZException):
    """Raised when authentication fails."""
    
    def __init__(self, message="Authentication failed."):
        self.message = message
        super().__init__(self.message)

class GameNotFoundError(GZException):
    """Raised when a game is not found."""
    
    def __init__(self, message="Game not found."):
        self.message = message
        super().__init__(self.message)

class RequestFailedError(GZException):
    """Raised when a request fails."""
    def __init__(self, message="Rquest failed ({status_code}): {reason} | {exception}.", status_code: int = None, exception=None, reason=None):
        self.status_code = status_code
        self.message = message
        self.exception = exception
        self.reason = reason
        super().__init__(self.message.format(status_code=status_code, exception=exception, reason=reason))

class StorageOperationError(GZException):
    """Raised when a storage operation fails."""
    def __init__(self, message="Storage operation failed: {exception}.", exception=None):
        self.message = message
        self.exception = exception
        super().__init__(self.message.format(exception=exception))


class RouterError(GZException):
    """Base class for router exceptions."""
    def __init__(self, message="Router error: {exception}.", exception=None):
        self.message = message
        self.exception = exception
        super().__init__(self.message.format(exception=exception))

class HandlerAlreadyRegisteredError(RouterError):
    """Raised when a handler is already registered."""
    def __init__(self, message="Handler [{handler}] already registered.", handler: callable = None):
        self.handler = handler
        super().__init__(message.format(handler=handler.__name__ if isinstance(handler, callable) else handler))

class HandlerNotRegisteredError(RouterError):
    """Raised when a handler is not registered."""
    def __init__(self, message="Handler [{handler}] not registered.", handler: callable = None):
        self.handler = handler
        super().__init__(message.format(handler=handler.__name__ if isinstance(handler, callable) else handler))

class EventTypeError(RouterError):
    """Raised when a event type is not valid."""
    def __init__(self, message="Event type [{event_type}] is not valid for the router {router}.", event_type: str = None, router: 'BaseRouter' = None):
        self.event_type = event_type
        super().__init__(message.format(event_type=event_type, router=router.__class__.__name__))


class DispatcherError(GZException):
    """Base class for dispatcher exceptions."""
    def __init__(self, message="Dispatcher error: {exception}.", exception=None):
        self.message = message
        self.exception = exception
        super().__init__(self.message.format(exception=exception))

class NoRoutersError(DispatcherError):
    """Raised when no routers are registered."""
    def __init__(self, message="No routers registered. You must register routers before performing this operation."):
        super().__init__(message)

class NoTrackersError(DispatcherError):
    """Raised when no trackers are registered."""
    def __init__(self, message="No trackers registered. You must register trackers before performing this operation."):
        super().__init__(message)

class DispatcherIsRunningError(DispatcherError):
    """Raised when a dispatcher is running (i.e. an operation is not supposed to be performed while the dispatcher is running or trying to start already running dispatcher)."""
    def __init__(self, message="Dispatcher is running. You must perform this operation while the dispatcher is not running."):
        super().__init__(message)

class RouterAlreadyRegisteredError(DispatcherError):
    """Raised when a router is already registered."""
    def __init__(self, message="Router [{router}] already registered.", router: 'BaseRouter' = None):
        super().__init__(message.format(handler=router.__class__.__name__ if isinstance(router, object) else router))

class RouterNotRegisteredError(DispatcherError):
    """Raised when a router is not registered."""
    def __init__(self, message="Router [{router}] not registered.", router: 'BaseRouter' = None):
        super().__init__(message.format(router=router.__class__.__name__ if isinstance(router, object) else router))

class TrackerAlreadyRegisteredError(DispatcherError):
    """Raised when a tracker is already registered."""
    def __init__(self, message="Tracker [{tracker}] already registered.", tracker: 'DispatchableTracker' = None):
        super().__init__(message.format(tracker=tracker.__class__.__name__ if isinstance(tracker, object) else tracker))

class TrackerNotRegisteredError(DispatcherError):
    """Raised when a tracker is not registered."""
    def __init__(self, message="Tracker [{tracker}] not registered.", tracker: 'DispatchableTracker' = None):
        super().__init__(message.format(tracker=tracker.__class__.__name__ if isinstance(tracker, object) else tracker))