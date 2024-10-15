from abc import abstractmethod, ABC
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Optional, Union
from pygzctfapi import models


NoticeUpdateTypes = SimpleNamespace(
    new='new',
    edited='edited',
    deleted='deleted'
)


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
    """Class to represent a notice update."""
    update_type: str
    new_notice: Optional[Union[models.Notice, dict]]
    old_notice: Optional[Union[models.Notice, dict]]

    @classmethod
    def from_dict(cls, data: dict) -> 'NoticeUpdate':
        """Creates a NoticeUpdate object from a dictionary."""
        new_notice = data['newNotice'] if 'newNotice' in data else None
        old_notice = data['oldNotice'] if 'oldNotice' in data else None
        if isinstance(new_notice, dict):
            new_notice = models.Notice.from_dict(new_notice)
        if isinstance(old_notice, dict):
            old_notice = models.Notice.from_dict(old_notice)
        return cls(
            update_type=data['updateType'],
            new_notice=new_notice,
            old_notice=old_notice,
        )
    
    @property
    def summary(self) -> str:
        """Returns the summary of the notice update."""
        if self.update_type == NoticeUpdateTypes.new:
            return f"New notice ID({self.new_notice.id}): [{self.new_notice.message}]"
        elif self.update_type == NoticeUpdateTypes.edited:
            return f'Notice [{self.old_notice.message}] ID({self.old_notice.id}) edited: [{self.new_notice.message}]'
        elif self.update_type == NoticeUpdateTypes.deleted:
            return f'Notice deleted ID({self.old_notice.id}): [{self.old_notice.message}]'
    
    @property
    def message(self) -> str:
        """Returns the message of the notice."""
        if self.update_type == NoticeUpdateTypes.new:
            return self.new_notice.message
        elif self.update_type == NoticeUpdateTypes.edited:
            return self.new_notice.message
        elif self.update_type == NoticeUpdateTypes.deleted:
            return self.old_notice.message
    
    @property
    def id(self) -> int:
        """Returns the ID of the notice."""
        if self.update_type == NoticeUpdateTypes.new:
            return self.new_notice.id
        elif self.update_type == NoticeUpdateTypes.edited:
            return self.new_notice.id
        elif self.update_type == NoticeUpdateTypes.deleted:
            return self.old_notice.id