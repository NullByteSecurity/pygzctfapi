from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class Game:
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
    
    def json(self, indent=None) -> str:
        """Converts the Game object to a JSON string."""
        return json.dumps(self, default=self._json_default, indent=indent)

    def _json_default(self, obj):
        """Helper method to convert non-serializable objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj.__dict__

    @staticmethod
    def from_dict(data: dict) -> 'Game':
        """Helper method to create Game object from a dictionary."""
        return Game(
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


@dataclass
class GameSummary:
    id: int
    title: str
    summary: str
    start: datetime
    end: datetime
    limit: int
    poster: str

    @staticmethod
    def from_dict(data: dict) -> 'GameSummary':
        """Helper method to create GameSummary object from a dictionary."""
        return GameSummary(
            id=data['id'],
            title=data['title'],
            summary=data['summary'],
            start=datetime.fromisoformat(data['start'].rstrip('Z')),
            end=datetime.fromisoformat(data['end'].rstrip('Z')),
            limit=data['limit'],
            poster=data['poster']
        )
        
    def __eq__(self, other):
        """Equality method to compare two GameSummary objects. Compared only by id."""
        if not isinstance(other, GameSummary):
            return False

        return self.id == other.id

    def json(self, indent=None) -> str:
        """Converts the GameSummary object to a JSON string."""
        return json.dumps(self, default=self._json_default, indent=indent)

    def _json_default(self, obj):
        """Helper method to convert non-serializable objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj.__dict__


@dataclass
class Profile:
    userId: str
    userName: str
    email: str
    avatar: str
    bio: str
    phone: str
    realName: str
    role: str
    stdNumber: str

    def json(self, indent=None) -> str:
        """Converts the Profile object to a JSON string."""
        return json.dumps(self, default=self._json_default, indent=indent)

    def _json_default(self, obj):
        """Helper method to convert non-serializable objects."""
        return str(obj)

    @staticmethod
    def from_dict(data: dict) -> 'Profile':
        """Helper method to create a Profile object from a dictionary."""
        return Profile(
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