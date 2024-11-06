from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Union
from urllib.parse import urlparse


@dataclass
class ListDiff:
    list1: list
    list2: list
    common: list
    unique1: list
    unique2: list


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

def list_diff(list1: list, list2: list) -> ListDiff:
    set1 = set(list1)
    set2 = set(list2)
    
    common_elements = list(set1 & set2)
    unique_to_list1 = list(set1 - set2)
    unique_to_list2 = list(set2 - set1)
    
    return ListDiff(list1, list2, common_elements, unique_to_list1, unique_to_list2)

def to_datetime(time: Union[int, float, datetime, str]) -> datetime:
    if isinstance(time, str):
        time = datetime.fromisoformat(time.rstrip('Z'))
    elif isinstance(time, int | float):
        time = datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        time = time.astimezone(timezone.utc)
    else:
        raise TypeError(f"Invalid type {type(time)} for time argument.")
    return time