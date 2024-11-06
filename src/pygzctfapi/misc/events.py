from typing import Any, Iterator


class Event:
    def __init__(self, event: str, data: Any):
        self.event = event
        self.data = data

    @property
    def summary(self) -> str:
        """Returns the summary of the event."""
        if hasattr(self.data, 'summary'):
            return f"Event ({self.event}): {self.data.summary}"
        else:
            return f"Event ({self.event})"
    
    def __str__(self) -> str:
        return self.summary


class BaseEventsClass:
    def __iter__(self) -> Iterator[str]:
        for attr in self.__dir__():
            if not attr.startswith('_'):
                yield getattr(self, attr)
        
class NoticeTrackerEvents(BaseEventsClass):
    @property
    def new(self):
        """Handle new notices."""
        return 'notice.new'
    
    @property
    def edited(self):
        """Handle edited notices."""
        return 'notice.edited'
    
    @property
    def deleted(self):
        """Handle deleted notices."""
        return 'notice.deleted'

    @property
    def any(self):
        """Handle any update on notices."""
        return 'notice.any'
