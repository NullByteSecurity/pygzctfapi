import httpx
from pygzctfapi import constants, utils, controllers, exceptions
from urllib.parse import urljoin
from collections import namedtuple

CREDSTUPLE = namedtuple("Credentials", "login password")

class GZAPI():

    def __init__(self, url: str, login: str = None, password: str = None):
        self._url = utils.domain_to_url(url)
        self._credentials = CREDSTUPLE(login, password) if login and password else None
        self._client = httpx.Client()
        self._client.headers= {
            'authority': utils.url_to_domain(self.platform_url),
            'origin': f'{self.platform_url[:-1]}',
        }
        self._client.headers.update(constants.DEFAULT_REQUEST_HEADERS)
        if self._credentials is not None:
            self.authenticate()
        
        #Controllers
        self.game = controllers.GameController(self)
        self.account = controllers.AccountController(self)
    
    @property
    def platform_url(self):
        return self._url
    
    @property
    def is_authenticated(self):
        try:
            return self.check_auth()
        except exceptions.NotAuthorizedError:
            return False
    
    def authenticate(self, login: str = None, password: str = None):
        if login is not None and password is not None:
            self._credentials = CREDSTUPLE(login, password)
        if self._credentials is None:
            raise exceptions.AuthenticationError("Credentials not provided")
        json_data = {
            'userName': self._credentials.login,
            'password': self._credentials.password,
        }
        response = self._client.post(f'{self.platform_url}api/account/login', headers=self._get_referer('account/login?from=/'), json=json_data)
        if response.status_code != 200:
            raise exceptions.AuthenticationError(f"Authentication failed with status code {response.status_code}, reason: {response.json()['title']}.")
        return True
        
    def check_auth(self, role='user', reauth=True):
        if self._client.cookies.get('GZCTF_Token') is not None:
            profile = self._client.get(self._build_url('api/account/profile'), headers=self._get_referer('account/profile'))
            if profile.status_code == 401:
                if reauth and self._credentials is not None:
                    self.authenticate()
                    return self.check_auth(role=role, reauth=False)
                raise exceptions.NotAuthorizedError(f"Authorization check failed with status code 401, reason: {profile.json()['title']}.")
            elif profile.status_code != 200:
                raise exceptions.NotAuthorizedError(f"Authorization check failed with status code {profile.status_code}, reason: {profile.json()['title']}.")
            if role.lower() != profile.json()['role'].lower():
                raise exceptions.NotAuthorizedError(f'You are not allowed to perform this action. You are {profile.json()["role"]} and you need to be {role}.')
            else:
                return True
        else:
            raise exceptions.NotAuthorizedError("This action requires authorization. You are not logged in.")

    def _build_url(self, *args):
        return urljoin(self.platform_url, *args)

    def _get_referer(self, path: str = ''):
        return { 'referer': self._build_url(path) }
