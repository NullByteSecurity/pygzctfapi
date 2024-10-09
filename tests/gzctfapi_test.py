from pygzctfapi import GZAPI
from icecream import ic

url = "https://games.nullbyte.pro/"
login = 'TEST'
password = 'T3STacc0UNT_j0Kkw3U!'

gzapi_unauth = GZAPI(url)
gzapi = GZAPI(url, login, password)

def test_game():
    print()
    #--- Test UNauthenticated
    games = gzapi_unauth.game.list()
    ic([game.title for game in games])
    ic(games[0].upgrade().title)
    eg = gzapi_unauth.game.get(title='Eternal Games')
    gzapi_unauth.game.get(2)
    assert len(notices := eg.notices()) == len(gzapi_unauth.game.notices(eg.id))
    ic(f"Eternal Games notices: {len(notices)}")

def test_account():
    print()
    #--- Test Authenticated
    ic((profile := gzapi.account.profile()).userName)
