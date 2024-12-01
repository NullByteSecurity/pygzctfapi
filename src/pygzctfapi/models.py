from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
from typing import List, Optional, Self
from urllib.parse import urljoin
from pygzctfapi import utils, variables

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygzctfapi import GZAPI


class BaseModel:
    def json(self, indent=None) -> str:
        """Converts the object to a JSON string."""
        return json.dumps(self, default=self._json_default, indent=indent)
    
    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Helper method to create a BaseModel object from a dictionary.
        
        Args:
            data (dict): The dictionary to create the object from.
        
        Returns:
            Self: The created BaseModel object.
        """
        return cls(**{key: data[key] for key in cls.__dataclass_fields__ if key in data})
    
    @staticmethod
    def _json_default(obj):
        """Helper method to convert non-serializable objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, BaseModel):
            return asdict(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class FunctionalModel(BaseModel):
    _gzapi: Optional['GZAPI'] = None
    
    def _set_gzapi(self, gzapi: Optional['GZAPI']):
        """Helper method to set the GZAPI object reference."""
        self._gzapi = gzapi
    
    @classmethod
    def from_dict(cls, data: dict, gzapi: Optional['GZAPI'] = None) -> Self:
        """Helper method to create a FunctionalModel object from a dictionary.
        
        Args:
            data (dict): The dictionary to create the object from.
            gzapi (GZAPI | None): The GZAPI object reference.
        
        Returns:
            Self: The created FunctionalModel object.
        """
        obj = cls(**{key: data[key] for key in cls.__dataclass_fields__ if key in data})
        obj._set_gzapi(gzapi)
        if "__post_init__" in obj.__dir__():
            obj.__post_init__()
        return obj

class UpgradeableModel(FunctionalModel):
    def upgrade(self):
        """Helper method to upgrade the object. Should return an upgraded object."""
        raise NotImplementedError

class UpdateableModel(FunctionalModel):
    def update(self) -> tuple[bool, list[str]]:
        """Helper method to update the object. Should update the object and return tuple (is_updated(bool), updated_fields(list))."""
        raise NotImplementedError
    
    def _update_from(self, new: Self) -> tuple[bool, list[str]]:
        """Update the object from another object of the same type.
        
        Args:
            new (Self): The object to update from.
        
        Returns:
            tuple: A tuple containing a boolean indicating if the object was updated and a list of updated fields.
        """
        changed = []
        for key, value in asdict(new).items():
            if key in self.__dataclass_fields__:
                if getattr(self, key) != value:
                    setattr(self, key, value)
                    changed.append(key)
        if "__post_init__" in self.__dir__():
            self.__post_init__()
        return (len(changed) > 0, changed)


@dataclass
class Game(UpdateableModel):
    id: int
    title: str
    content: str
    summary: str
    start: datetime
    end: datetime
    status: str
    teamCount: int
    hidden: bool
    inviteCodeRequired: bool
    limit: int
    practiceMode: bool
    writeupRequired: bool
    division: str
    divisions: str
    poster: str
    teamName: str
    
    def __post_init__(self):
        if isinstance(self.start, str):
            self.start = datetime.fromisoformat(self.start.rstrip('Z'))
        if isinstance(self.end, str):
            self.end = datetime.fromisoformat(self.end.rstrip('Z'))
        if self._gzapi is not None:
            if isinstance(self.poster, str) and not self.poster.startswith('http'):
                self.poster = urljoin(self._gzapi.platform_url, self.poster)
    
    def update(self) -> tuple[bool, list[str]]:
        """Update the object.
        
        Returns:
            tuple: A tuple containing a boolean indicating if the object was updated and a list of updated fields.
        """
        new = self._gzapi.game._get_by_id(self.id)
        return self._update_from(new)
        
    def notices(self) -> List['Notice']:
        """
        Get a list of notices for the game.

        Returns:
            List[Notice]: A list of Notice objects
        """
        return self._gzapi.game.notices(game_id=self.id)


@dataclass
class GameSummary(UpgradeableModel, UpdateableModel):
    id: int
    title: str
    summary: str
    start: datetime
    end: datetime
    limit: int
    poster: str
    
    def __post_init__(self):
        if isinstance(self.start, str):
            self.start = datetime.fromisoformat(self.start.rstrip('Z'))
        if isinstance(self.end, str):
            self.end = datetime.fromisoformat(self.end.rstrip('Z'))
        if self._gzapi is not None:
            if isinstance(self.poster, str) and not self.poster.startswith('http'):
                self.poster = urljoin(self._gzapi.platform_url, self.poster)
    
    def upgrade(self) -> 'Game':
        """Upgrade the object to a full Game object.
        
        Returns:
            Game: The full Game object.
        """
        return self._gzapi.game._get_by_id(self.id)
    
    def update(self) -> tuple[bool, list[str]]:
        """Update the object.
        
        Returns:
            tuple: A tuple containing a boolean indicating if the object was updated and a list of updated fields.
        """
        new = self._gzapi.game._get_by_id(self.id)
        return self._update_from(new)


@dataclass
class Profile(BaseModel):
    userId: str
    userName: str
    email: str
    avatar: str
    bio: str
    phone: str
    realName: str
    role: str
    stdNumber: str
    

@dataclass
class Notice(BaseModel):
    id: int
    time: datetime
    type: str
    values: List[str]
    
    def __post_init__(self):
        if not isinstance(self.time, datetime):
            self.time = utils.to_datetime(self.time)
    
    @property
    def message(self) -> str:
        """Returns the message of the notice."""
        match self.type:
            case 'Normal':
                return variables.NOTICES_TEXTS[self.type].format(notice=self.values[0])
            case 'NewChallenge':
                return variables.NOTICES_TEXTS[self.type].format(challenge=self.values[0])
            case "NewHint":
                return variables.NOTICES_TEXTS[self.type].format(challenge=self.values[0])
            case _ if self.type.endswith('Blood'):
                return variables.NOTICES_TEXTS[self.type].format(team=self.values[0], blood=self.type[:-5].lower(), challenge=self.values[1])
            case _:
                return variables.NOTICES_TEXTS['_'].format(type=self.type, values=' '.join(self.values))
