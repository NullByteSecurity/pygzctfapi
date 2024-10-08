from typing import List
from urllib.parse import urljoin
from pygzctfapi import exceptions
from pygzctfapi import models

class BaseController():
    def __init__(self, gzapi, endpoint, endpoint_name):
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
    
    def _build_url(self, *paths) -> str:
        """
        Build a URL by joining self._endpoint_url with the given arguments.
        Args:
            *paths: URL path segments to join
        Returns:
            str: The joined URL
        """
        result = self._endpoint_url + ('/' if self._endpoint_url[-1] != '/' else '')
        for path in paths:
            path = path.strip('/')
            result = urljoin(result, path + '/')
        return result.rstrip('/')

class GameController(BaseController):
    def __init__(self, gzapi):
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
        games = [models.GameSummary.from_dict(game) for game in response.json()]
        for game in games:
            game.poster = urljoin(self._gzapi.platform_url, game.poster) if game.poster else None
            game.set_gzapi(self._gzapi)
        return games

    def get(self, gameId: int = None, title: str = None) -> models.Game:
        """
        Get a game by its ID or title.

        Args:
            gameId (int, optional): The ID of the game. Defaults to None.
            title (str, optional): The title of the game. Defaults to None.

        Returns:
            models.Game: The game
        """
        if gameId is None and title is None:
            raise ValueError("Either id or title must be provided.")
        if gameId is not None:
            return self._get_by_id(gameId)
        return self._get_by_title(title)
    
    def notices(self, gameId: int) -> List[models.Notice]:
        response = self._gzapi._client.get(self._build_url(str(gameId), '/notices'), headers=self._gzapi._get_referer(f'games/{gameId}/challenges'))
        exceptions.Raiser.raise_for_status(response)
        from icecream import ic
        ic(response.url)
        notices = [models.Notice.from_dict(notice) for notice in response.json()]
        return notices
    
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
                return self.get(game.id)
        raise exceptions.GameNotFoundError(f"Game with title \"{title}\" not found.")
    
    def _get_by_id(self, gameId: int) -> models.Game:
        """
        Get a game by its ID.

        Args:
            gameId (int): The ID of the game

        Returns:
            models.Game: The game

        Raises:
            exceptions.GameNotFoundError: If the game is not found
        """
        response = self._gzapi._client.get(self._build_url(str(gameId)), headers=self._gzapi._get_referer('games'))
        exceptions.Raiser.raise_for_status(response)
        if response.status_code == 404:
            raise exceptions.GameNotFoundError(f"Game with id {gameId} not found.")
        game = models.Game.from_dict(response.json())
        game.poster = urljoin(self._gzapi.platform_url, game.poster) if game.poster else None
        return game
        
class AccountController(BaseController):
    def __init__(self, gzapi):
        """
        Initialize the AccountController with the given GZAPI instance.

        Args:
            gzapi (GZAPI): The GZAPI instance to use for requests
        """
        super().__init__(gzapi, '/api/account', 'account')
    
    def profile(self) -> models.Profile:
        """
        Get the profile of the logged-in user.

        Returns:
            models.Profile: The profile of the logged-in user

        Raises:
            exceptions.NotAuthorizedError: If the user is not logged in
        """
        self._gzapi.check_auth()
        response = self._gzapi._client.get(self._build_url('profile'), headers=self._gzapi._get_referer('account/profile'))
        exceptions.Raiser.raise_for_status(response)
        profile = models.Profile.from_dict(response.json())
        profile.avatar = urljoin(self._gzapi.platform_url, profile.avatar) if profile.avatar else None
        return profile