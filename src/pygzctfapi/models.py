from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
from typing import List
from pygzctfapi import utils, variables

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygzctfapi import GZAPI

@dataclass
class BaseModel:
    def json(self, indent=None) -> str:
        """Converts the object to a JSON string."""
        return json.dumps(self, default=self._json_default, indent=indent)
    
    @staticmethod
    def _json_default(obj):
        """Helper method to convert non-serializable objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, BaseModel):
            return asdict(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

@dataclass
class FunctionalModel(BaseModel):
    _gzapi: 'GZAPI' = field(default=None, repr=False, init=False)
    
    def set_gzapi(self, gzapi: 'GZAPI'):
        """Helper method to set the GZAPI object reference."""
        self._gzapi = gzapi

@dataclass
class UpgradeableModel(FunctionalModel):
    def upgrade(self):
        """Helper method to upgrade the object."""
        raise NotImplementedError


@dataclass
class Game(FunctionalModel):
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
    organization: str
    organizations: str
    poster: str
    teamName: str

    @classmethod
    def from_dict(cls, data: dict) -> 'Game':
        """Helper method to create Game object from a dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            summary=data['summary'],
            start=datetime.fromisoformat(data['start'].rstrip('Z')),
            end=datetime.fromisoformat(data['end'].rstrip('Z')),
            status=data['status'],
            teamCount=data['teamCount'],
            hidden=data['hidden'],
            inviteCodeRequired=data['inviteCodeRequired'],
            limit=data['limit'],
            practiceMode=data['practiceMode'],
            writeupRequired=data['writeupRequired'],
            organization=data['organization'],
            organizations=data['organizations'],
            poster=data['poster'],
            teamName=data['teamName']
        )
    
    def __eq__(self, other):
        """Equality method to compare two Game objects. Compared only by id."""
        if not isinstance(other, Game):
            return False

        return self.id == other.id
    
    def notices(self) -> List['Notice']:
        """
        Get a list of notices for the game.

        Returns:
            List[Notice]: A list of Notice objects
        """
        return self._gzapi.game.notices(game_id=self.id)


@dataclass
class GameSummary(UpgradeableModel):
    id: int
    title: str
    summary: str
    start: datetime
    end: datetime
    limit: int
    poster: str

    @classmethod
    def from_dict(cls, data: dict) -> 'GameSummary':
        """Helper method to create GameSummary object from a dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            summary=data['summary'],
            start=datetime.fromisoformat(data['start'].rstrip('Z')),
            end=datetime.fromisoformat(data['end'].rstrip('Z')),
            limit=data['limit'],
            poster=data['poster']
        )
        
    def upgrade(self) -> 'Game':
        """Upgrade the object to a full Game object.
        
        Returns:
            Game: The full Game object.
        """
        return self._gzapi.game._get_by_id(self.id)
        
    def __eq__(self, other):
        """Equality method to compare two GameSummary objects. Compared only by id."""
        if not isinstance(other, GameSummary):
            return False

        return self.id == other.id


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

    @classmethod
    def from_dict(cls, data: dict) -> 'Profile':
        """Helper method to create a Profile object from a dictionary."""
        return cls(
            userId=data['userId'],
            userName=data['userName'],
            email=data['email'],
            avatar=data['avatar'],
            bio=data['bio'],
            phone=data['phone'],
            realName=data['realName'],
            role=data['role'],
            stdNumber=data['stdNumber']
        )
    
    def __eq__(self, other):
        """Equality method to compare two Profile objects. Compared only by id."""
        if not isinstance(other, Profile):
            return False

        return self.userId == other.userId

@dataclass
class Notice(BaseModel):
    id: int
    time: datetime
    type: str
    values: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> 'Notice':
        """Creates a Notice object from a dictionary."""
        return cls(
            id=data['id'],
            time=utils.to_datetime(data['time']),
            type=data['type'],
            values=data['values']
        )
    
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
