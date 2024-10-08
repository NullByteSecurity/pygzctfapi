import httpx
from pygzctfapi import constants, utils, controllers, exceptions
from pygzctfapi.classes import GZAPIBaseClass
from urllib.parse import urljoin
from collections import namedtuple

CREDSTUPLE = namedtuple("Credentials", "login password")

class GZAPI(GZAPIBaseClass):

    def __init__(self, url: str, login: str = None, password: str = None):
        """
        Initialize a GZAPI object.

        Args:
            url (str): The URL of the GZCTF instance.
            login (str, optional): The login to use for authentication. Defaults to None.
            password (str, optional): The password to use for authentication. Defaults to None.

        Raises:
            exceptions.AuthenticationError: If authentication fails.
            ValueError: If url is not a valid URL.
        """
        if not utils.validate_url(url):
            raise ValueError("Given platform URL is not valid.")
        self._url = url + ('/' if url[-1] != '/' else '')
        self._credentials = CREDSTUPLE(login, password) if login and password else None
        self._client = httpx.Client()
        self._client.headers= {
            'authority': utils.url_to_domain(url),
            'origin': f'{utils.domain_to_url(url, enclosing=False)}',
        }
        self._client.headers.update(constants.DEFAULT_REQUEST_HEADERS)
        if self._credentials is not None:
            self.authenticate()
        
        #Controllers
        self.game = controllers.GameController(self)
        self.account = controllers.AccountController(self)
    
    @property
    def platform_url(self) -> str:
        """
        The URL of the GZCTF instance.
        
        Returns:
            str: The URL of the GZCTF instance.
        """
        return self._url
    
    @property
    def is_authenticated(self) -> bool:
        """
        Check if the user is authenticated.

        Returns:
            bool: True if the user is authenticated, False otherwise.
        """
        try:
            return self.check_auth()
        except exceptions.NotAuthorizedError:
            return False
    
    def authenticate(self, login: str = None, password: str = None) -> bool:
        """
        Authenticate the user with the provided credentials or takes the credentials provided during the object initialization.

        Args:
            login (str, optional): The login to use for authentication. Defaults to None.
            password (str, optional): The password to use for authentication. Defaults to None.

        Returns:
            bool: True if the authentication was successful.

        Raises:
            exceptions.AuthenticationError: If authentication fails.
        """
       
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
        
    def check_auth(self, role='user', reauth=True) -> bool:
        """
        Check if the user is authorized to perform an action.

        Args:
            role (str, optional): The role required to perform the action. Defaults to 'user'.
            reauth (bool, optional): If set to True, the user will be re-authenticated if the session has expired. Defaults to True.

        Returns:
            bool: True if the user role is equal or higher than the required role.

        Raises:
            exceptions.NotAuthorizedError: If the user role is lower than the required role or if the authorization check fails.
        """
        if self._client.cookies.get('GZCTF_Token') is not None:
            profile = self._client.get(self._build_url('api/account/profile'), headers=self._get_referer('account/profile'))
            if profile.status_code == 401:
                if reauth and self._credentials is not None:
                    self.authenticate()
                    return self.check_auth(role=role, reauth=False)
                raise exceptions.NotAuthorizedError(f"Authorization check failed with status code 401, reason: {profile.json()['title']}.")
            elif profile.status_code != 200:
                raise exceptions.NotAuthorizedError(f"Authorization check failed with status code {profile.status_code}, reason: {profile.json()['title']}.")
            if constants.ROLES.index(role.lower()) > constants.ROLES.index(profile.json()['role'].lower()):
                raise exceptions.NotAuthorizedError(f'You are not allowed to perform this action. You are {profile.json()["role"]} and you need to be {role.capitalize()} or higher.')
            else:
                return True
        else:
            raise exceptions.NotAuthorizedError("This action requires authorization. You are not logged in.")

    def _build_url(self, *args) -> str:
        """
        Build a URL by joining self.platform_url with the given arguments.
        Args:
            *args: URL path segments to join
        Returns:
            str: The joined URL
        """
        return urljoin(self.platform_url, *args)

    def _get_referer(self, path: str = '') -> dict:
        """
        Return a dictionary with the referer header set to the given path.

        Args:
            path (str): The path to use for the referer header. Defaults to an empty string.

        Returns:
            dict: A dictionary with the referer header
        """
        return { 'referer': self._build_url(path) }
