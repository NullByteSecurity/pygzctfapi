from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional, Union
from pygzctfapi import models
from pygzctfapi.misc.events import NoticeEvents


@dataclass
class BaseUpdate(ABC):
    """Class to represent a base update."""
    update_type: str
    
    @property
    @abstractmethod
    def summary(self) -> str:
        """Returns the summary of the update."""
        raise NotImplementedError


@dataclass
class NoticeUpdate(models.BaseModel):
    """Class to represent a notice update.
    
    Attributes:
        event (str): The event type.
        new_notice (Optional[models.Notice]): The new notice.
        old_notice (Optional[models.Notice]): The old notice.
    """
    event: str
    new_notice: Optional[models.Notice]
    old_notice: Optional[models.Notice]

    @classmethod
    def from_dict(cls, data: dict) -> 'NoticeUpdate':
        """Creates a NoticeUpdate object from a dictionary."""
        new_notice = data['new_notice'] if 'new_notice' in data else None
        old_notice = data['old_notice'] if 'old_notice' in data else None
        if isinstance(new_notice, dict):
            new_notice = models.Notice.from_dict(new_notice)
        if isinstance(old_notice, dict):
            old_notice = models.Notice.from_dict(old_notice)
        return cls(
            event=data['event'],
            new_notice=new_notice,
            old_notice=old_notice,
        )
    
    @property
    def summary(self) -> str:
        """Returns the summary of the notice update."""
        if self.event == NoticeEvents.NEW:
            return f"New notice ID({self.new_notice.id}): [{self.new_notice.message}]"
        elif self.event == NoticeEvents.EDITED:
            return f'Notice [{self.old_notice.message}] ID({self.old_notice.id}) edited: [{self.new_notice.message}]'
        elif self.event == NoticeEvents.DELETED:
            return f'Notice deleted ID({self.old_notice.id}): [{self.old_notice.message}]'
    
    @property
    def message(self) -> str:
        """Returns the message of the notice."""
        if self.event == NoticeEvents.NEW:
            return self.new_notice.message
        elif self.event == NoticeEvents.EDITED:
            return self.new_notice.message
        elif self.event == NoticeEvents.DELETED:
            return self.old_notice.message
    
    @property
    def id(self) -> int:
        """Returns the ID of the notice."""
        if self.event == NoticeEvents.NEW:
            return self.new_notice.id
        elif self.event == NoticeEvents.EDITED:
            return self.new_notice.id
        elif self.event == NoticeEvents.DELETED:
            return self.old_notice.id