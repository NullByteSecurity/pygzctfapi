from urllib.parse import urlparse


def url_to_domain(url: str) -> str:
    """
    Extract the domain from a URL. If the URL does not contain a scheme, return the input as-is.
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc if parsed_url.scheme else url.split('/')[0]


def domain_to_url(domain: str, scheme: str = "https", enclosing: bool = True) -> str:
    """
    Convert a domain to a complete URL with the given scheme. Optionally, add a trailing slash.
    """
    url = f"{scheme.rstrip('://')}://{url_to_domain(domain)}"
    
    # Add trailing slash if 'enclosing' is True
    return url + ('/' if enclosing else '')
