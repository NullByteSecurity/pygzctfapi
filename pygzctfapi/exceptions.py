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