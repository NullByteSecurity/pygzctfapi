from typing import List, Union
from pygzctfapi.misc.storages import InMemoryStorage
from pygzctfapi.models import Notice
from threading import Lock

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygzctfapi import GZAPI
    from pygzctfapi.misc.storages import StorageBaseClass
    from pygzctfapi.models import Game


#TODO: add support for callbacks, get_updates() should return NoticeUpdate objects (update_type, new_notice, old_notice), track all changes (including edits and deletions), add argument to disable tracking all changes except new notices
class NoticesTracker:
    def __init__(self, game: 'Game', storage: 'StorageBaseClass'=None, ignore_old_notices: bool=True, tracker_id: Union[str, int]=1, gzapi: 'GZAPI'=None, game_id: int=None):
        """
        Initialize the NoticesTracker.
        
        NoticesTracker tracks notices changes in a game. It supports polling [and callbacks based on polling (not yet)].
        To keep tracking changes after restarts, use Redis, LevelDB, or SQLite storages.

        Args:
            game (Game): The game to track. Mutually exclusive with (gzapi, game_id).
            storage (StorageBaseClass, optional): The storage to use. New InMemoryStorage will be created if not provided.
            ignore_old_notices (bool, optional): Whether to ignore old notices on first initialization. Defaults to True.
            tracker_id (Union[str, int], optional): The tracker ID used to distinguish multiple trackers by the same game. Defaults to 1.
            gzapi (GZAPI, optional): The GZAPI instance to use. Mutually exclusive with game.
            game_id (int, optional): The ID of the game to track. Mutually exclusive with game.

        Raises:
            RuntimeError: If either game or (gzapi, game_id) is not provided.
        """
        if game is not None:
            self._game = game
            self._gzapi = game._gzapi
        elif gzapi is not None and game_id is not None:
            self._gzapi = gzapi
            self._game = gzapi.game.get(game_id)
        else:
            raise RuntimeError("Either game or (gzapi, game_id) must be provided.")
        
        if storage is None:
            self._storage = InMemoryStorage()
        else:
            self._storage = storage
        self._lock = Lock()
        self._tracker_id = tracker_id
        self._store_key = f'NoticesTracker{tracker_id}-Game{self._game.id}-LNID'
        if ignore_old_notices and self._storage.get(self._store_key) is None:
            self.get_updates()
    
    @property
    def last_nid(self) -> int:
        """
        The last notice ID that was retrieved.

        The last notice ID that was retrieved the last time get_updates() was called.
        If get_updates() has not been called yet, this property will be 0 or the actual last notice ID retrieved on initialization, depending on ignore_old_notices.
        """
        notice_id = self._storage.get(self._store_key)
        return notice_id if notice_id is not None else 0
    
    @last_nid.setter
    def last_nid(self, notice_id: int):
        self._storage.set(self._store_key, notice_id)
    
    def get_updates(self, limit=None) -> List[Notice]:
        """
        Get a list of new notices since the last call of this method (or start of the program).

        Args:
            limit (int, optional): The maximum number of notices to return. Defaults to None.

        Returns:
            List: A list of Notice objects.
        """
        lnid = self.last_nid
        new_notices = list(filter(lambda notice: notice.id > lnid, self._game.notices()))
        if limit is not None:
            new_notices = new_notices[:limit]
        if len(new_notices) != 0:
            self.last_nid = new_notices[-1].id  #ATTENTION: not using max() cause filter() should preserve the order
        return new_notices