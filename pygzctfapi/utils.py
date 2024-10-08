from urllib.parse import urlparse


def url_to_domain(url: str) -> str:
    """
    Convert a URL to a domain.

    Args:
        url (str): The URL to be converted.

    Returns:
        str: The domain of the URL.
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc if parsed_url.scheme else url.split('/')[0]


def domain_to_url(domain: str, scheme: str = "https", enclosing: bool = True) -> str:
    """
    Convert a domain to a URL.

    Args:
        domain (str): The domain to be converted.
        scheme (str, optional): The scheme to use for the URL. Defaults to 'https'.
        enclosing (bool, optional): Whether to add a trailing slash to the URL. Defaults to True.

    Returns:
        str: The URL
    """
    url = f"{scheme.rstrip(':/')}://{url_to_domain(domain)}"
    return url + ('/' if enclosing else '')

def validate_url(url: str) -> bool:
    """
    Validate whether a given URL is valid or not.

    Args:
        url (str): The URL to be validated

    Returns:
        bool: True if the URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
