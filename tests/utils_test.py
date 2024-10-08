from pygzctfapi import utils
from icecream import ic

domain = "games.nullbyte.pro"
url = "https://games.nullbyte.pro/"

def test_to_domain():
    assert utils.url_to_domain(url) == domain

def test_to_url():
    assert utils.domain_to_url(domain) == f"https://{domain}/"
    assert utils.domain_to_url(domain, scheme='http') == f"http://{domain}/"
    assert utils.domain_to_url(domain, enclosing=False) == f"https://{domain}"
    assert utils.validate_url(url)
    assert not utils.validate_url('google.com')
