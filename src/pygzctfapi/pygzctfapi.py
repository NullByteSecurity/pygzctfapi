import httpx
from pygzctfapi import constants, utils, controllers, exceptions
from urllib.parse import urljoin
    

class GZAPI:

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
        self._client = httpx.Client()
        self._client.headers= {
            'authority': utils.url_to_domain(url),
            'origin': f'{utils.domain_to_url(url, enclosing=False)}',
        }
        self._client.headers.update(constants.DEFAULT_REQUEST_HEADERS)
        self.authmgr = AuthManager(self, login, password)
        if self.authmgr.has_credentials:
            self.authmgr.authenticate()
        
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


class AuthManager:
    def __init__(self, gzapi: 'GZAPI', login: str = None, password: str = None):
        self._gzapi = gzapi
        self.__login = login
        self.__password = password
        if self.has_credentials:
            self.authenticate()
    
    @property
    def credentials(self) -> tuple[str, str]:
        return self.__login, self.__password
    
    @property
    def has_credentials(self) -> bool:
        return self.__login is not None and self.__password is not None
    
    @property
    def _client(self) -> httpx.Client:
        return self._gzapi._client
    
    @property
    def token(self) -> str:
        return self._client.cookies.get('GZCTF_Token')
    
    @token.setter
    def token(self, token: str):
        self._client.cookies.set('GZCTF_Token', token)
    
    @property
    def is_authenticated(self) -> bool:
        return self.get_role(reauth=False) != constants.Roles.GUEST
    
    def set_credentials(self, login: str, password: str):
        """
        Set the credentials to use for authentication.
        
        This method terminates the current session and clears any existing cookies.

        Args:
            login (str): The login to use for authentication.
            password (str): The password to use for authentication.

        Returns:
            None
        """
        self.__login = login
        self.__password = password
        self._client.cookies.clear()

    def authenticate(self) -> bool:
        """
        Authenticate the user with the saved credentials.

        Returns:
            bool: True if the authentication was successful.

        Raises:
            exceptions.AuthenticationError: If authentication fails or credentials are not set.
        """
       
        if not self.has_credentials:
            raise exceptions.AuthenticationError("Credentials are not set.")
        json_data = {
            'userName': self.__login,
            'password': self.__password,
        }
        response = self._client.post(f'{self._gzapi.platform_url}api/account/login', headers=self._gzapi._get_referer('account/login?from=/'), json=json_data)
        if response.status_code != 200:
            raise exceptions.AuthenticationError(f"Authentication failed with status code {response.status_code}, reason: {response.text}.")
        return True

    def reauthenticate(self):
        return self.authenticate()
    
    def get_role(self, reauth=True) -> str:
        """
        Get the role of the current session.

        Args:
            reauth (bool, optional): Whether to re-authenticate if the session has expired (only if login and password are set). Defaults to True.

        Returns:
            str: The role of the currently logged-in user. If the user is not logged in, returns constants.Roles.GUEST

        Raises:
            exceptions.RequestFailedError: If the request fails with a status code other than 200 or 401.
        """
        if self.token is not None:
            profile = self._client.get(self._gzapi._build_url('api/account/profile'), headers=self._gzapi._get_referer('account/profile'))
            if profile.status_code == 401:
                if reauth and self.has_credentials:
                    self.authenticate()
                    return self.get_role(reauth=False)
                else:
                    return constants.Roles.GUEST
            elif profile.status_code != 200:
                raise exceptions.RequestFailedError(message=f"Role retrieval failed with status code {profile.status_code}, reason: {profile.text}.", status_code=profile.status_code, reason=profile.text)
            return constants.Roles(profile.json()['role'].lower())
        else:
            return constants.Roles.GUEST
    
    def raise_on_insufficient_role(self, required_role='user', reauth=True) -> bool:
        """
        Check if the current session has the required or higher role permissions.

        Args:
            required_role (str, optional): The required session role. Defaults to 'user'.
            reauth (bool, optional): Whether to re-authenticate if the session has expired (only if login and password are set). Defaults to True.

        Returns:
            bool: True if the session role is equal or higher than the required role.

        Raises:
            exceptions.NotAuthorizedError: If the session role is lower than the required role.
        """
        current_role = self.get_role(reauth=reauth)
        if constants.ROLES.index(current_role) < constants.ROLES.index(required_role.lower()):
            raise exceptions.NotAuthorizedError(f'You are not allowed to perform this action. You are {current_role.capitalize()} and you need to be {required_role.capitalize()} or higher.')
        else:
            return True
