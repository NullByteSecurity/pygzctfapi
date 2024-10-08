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
    ic(games := gzapi_unauth.game.list())
    ic(games[0].upgrade())
    ic(game_by_name := gzapi_unauth.game.get(title='Eternal Games'))
    ic(game_by_id := gzapi_unauth.game.get(2))

def test_account():
    #--- Test Authenticated
    ic(profile := gzapi.account.profile())
    ic(notices := gzapi.game.notices(1))
    ic([notice.message for notice in notices])
