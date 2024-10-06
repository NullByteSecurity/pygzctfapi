from pygzctfapi import GZAPI
from icecream import ic

url = "https://games.nullbyte.pro/"
login = 'TEST'
password = 'T3STacc0UNT_j0Kkw3U!'

def test_init():
    #--- Test UNauthenticated
    gzapi = GZAPI(url)
    #games
    ic(games := gzapi.game.list())
    ic(game_by_name := gzapi.game.get_by_title('Eternal Games'))
    ic(game_by_id := gzapi.game.get(2))
    
    #--- Test Authenticated
    gzapi = GZAPI(url, login, password)
    ic(profile := gzapi.account.profile())
