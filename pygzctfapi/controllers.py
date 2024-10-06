from urllib.parse import urljoin
from pygzctfapi import exceptions

class BaseController():
    def __init__(self, gzapi, endpoint, endpoint_name):
        self._gzapi = gzapi
        self._endpoint = endpoint
        self._endpoint_name = endpoint_name
        self._endpoint_url = urljoin(self._gzapi.platform_url, self._endpoint)
    
    def _build_url(self, *args):
        return urljoin(self._endpoint_url, *args)

class GameController(BaseController):
    def __init__(self, gzapi):
        super().__init__(gzapi, '/api/game/', 'game')
    
    def list(self):
        response = self._gzapi._client.get(self._endpoint_url, headers=self._gzapi._get_referer('game'))
        #TODO: create and use models
        return response.json()
    
    def get_by_name(self, name: str):
        games = self.list()
        for game in games:
            if game['title'] == name:
                return self.get(game['id'])
        raise exceptions.GameNotFoundError(f"Game {name} not found.")
    
    def get(self, id: int):
        response = self._gzapi._client.get(self._build_url(str(id)), headers=self._gzapi._get_referer('game'))
        #TODO: create and use models
        return response.json()
        

class AccountController(BaseController):
    def __init__(self, gzapi):
        super().__init__(gzapi, '/api/account/', 'account')
    
    def profile(self):
        self._gzapi.check_auth()
        response = self._gzapi._client.get(self._build_url('profile'), headers=self._gzapi._get_referer('account/profile'))
        #TODO: create and use models
        return response.json()