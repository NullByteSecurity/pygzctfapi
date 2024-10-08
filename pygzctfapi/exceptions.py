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