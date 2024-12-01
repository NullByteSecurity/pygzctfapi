from typing import List
from urllib.parse import urljoin
from pygzctfapi import exceptions
from pygzctfapi import models

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pygzctfapi import GZAPI

class BaseController():
    def __init__(self, gzapi: 'GZAPI', endpoint: str, endpoint_name: str):
        """
        Initialize the controller with the given GZAPI instance, endpoint, and endpoint name.

        Args:
            gzapi (GZAPI): The GZAPI instance to use for requests
            endpoint (str): The URL endpoint for the controller
            endpoint_name (str): The name of the endpoint
        """
        self._gzapi = gzapi
        self._endpoint = endpoint
        self._endpoint_name = endpoint_name
        self._endpoint_url = urljoin(self._gzapi.platform_url, self._endpoint)
    
    def _build_url(self, *paths: str) -> str:
        """
        Build a URL by joining self._endpoint_url with the given arguments.
        Args:
            *paths (str): URL path segments to join
        Returns:
            str: The joined URL
        """
        result = self._endpoint_url + ('/' if self._endpoint_url[-1] != '/' else '')
        for path in paths:
            path = path.strip('/')
            result = urljoin(result, path + '/')
        return result.rstrip('/')

class GameController(BaseController):
    def __init__(self, gzapi: 'GZAPI'):
        """
        Initialize the GameController with the given GZAPI instance.

        Args:
            gzapi (GZAPI): The GZAPI instance to use for requests
        """
        super().__init__(gzapi, '/api/game', 'game')
    
    def list(self) -> List[models.GameSummary]:
        """
        Get a list of games.

        Returns:
            list[models.GameSummary]: A list of games
        """
        response = self._gzapi._client.get(self._endpoint_url, headers=self._gzapi._get_referer('games'))
        exceptions.Raiser.raise_for_status(response)
        games = sorted([models.GameSummary.from_dict(game, self._gzapi) for game in response.json()], key=lambda game: game.id)
        return games

    def get(self, game_id: int = None, title: str = None) -> models.Game:
        """
        Get a game by its ID or title.

        Args:
            game_id (int, optional): The ID of the game. Defaults to None.
            title (str, optional): The title of the game. Defaults to None.

        Returns:
            models.Game: The game
        """
        if game_id is None and title is None:
            raise ValueError("Either game_id or title must be provided.")
        if game_id is not None:
            return self._get_by_id(game_id)
        return self._get_by_title(title)
    
    def _get_by_title(self, title: str) -> models.Game:
        """
        Get a game by its title.

        Args:
            title (str): The title of the game

        Returns:
            models.Game: The game

        Raises:
            exceptions.GameNotFoundError: If the game is not found
        """
        games = self.list()
        for game in games:
            if game.title == title:
                return self._get_by_id(game.id)
        raise exceptions.GameNotFoundError(f"Game with title \"{title}\" not found.")
    
    def _get_by_id(self, game_id: int) -> models.Game:
        """
        Get a game by its ID.

        Args:
            game_id (int): The ID of the game

        Returns:
            models.Game: The game

        Raises:
            exceptions.GameNotFoundError: If the game is not found
        """
        response = self._gzapi._client.get(self._build_url(str(game_id)), headers=self._gzapi._get_referer('games'))
        exceptions.Raiser.raise_for_status(response)
        if response.status_code == 404:
            raise exceptions.GameNotFoundError(f"Game with id {game_id} not found.")
        game = models.Game.from_dict(response.json(), self._gzapi)
        return game
    
    def notices(self, game_id: int) -> List[models.Notice]:
        """
        Get a list of notices for a game.

        Args:
            game_id (int): The ID of the game

        Returns:
            List[models.Notice]: A list of Notice objects
        """
        response = self._gzapi._client.get(self._build_url(str(game_id), '/notices'), headers=self._gzapi._get_referer(f'games/{game_id}/challenges'))
        exceptions.Raiser.raise_for_status(response)
        notices = sorted([models.Notice.from_dict(notice) for notice in response.json()], key=lambda notice: notice.id)
        return notices
        
class AccountController(BaseController):
    def __init__(self, gzapi: 'GZAPI'):
        """
        Initialize the AccountController with the given GZAPI instance.

        Args:
            gzapi (GZAPI): The GZAPI instance to use for requests
        """
        super().__init__(gzapi, '/api/account', 'account')
    
    def profile(self) -> models.Profile:
        """
        Get the profile of the current user (session).

        Returns:
            models.Profile: The profile of the current user (session)

        Raises:
            exceptions.NotAuthorizedError: If the current session is a guest session (not logged in)
        """
        self._gzapi.authmgr.raise_on_insufficient_role()
        response = self._gzapi._client.get(self._build_url('profile'), headers=self._gzapi._get_referer('account/profile'))
        exceptions.Raiser.raise_for_status(response)
        profile = models.Profile.from_dict(response.json())
        profile.avatar = urljoin(self._gzapi.platform_url, profile.avatar) if profile.avatar else None
        return profile