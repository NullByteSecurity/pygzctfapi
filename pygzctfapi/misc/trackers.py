from dataclasses import asdict
from typing import List, Optional, Union
from pygzctfapi.misc.storages import InMemoryStorage
from pygzctfapi.misc.models import NoticeUpdate, NoticeUpdateTypes
from pygzctfapi.models import Notice
from pygzctfapi import utils
from threading import Lock

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygzctfapi import GZAPI
    from pygzctfapi.misc.storages import StorageBaseClass
    from pygzctfapi.models import Game


#TODO: add support for callbacks, get_updates() should be reviewed and tested
class NoticesTracker:
    def __init__(self, game: 'Game', storage: 'StorageBaseClass'=None, ignore_old_notices: bool=True, tracker_id: Union[str, int]=1):
        """
        Initialize the NoticesTracker.
        
        NoticesTracker tracks notices changes in a game. It supports polling [and callbacks based on polling (not yet)].
        To keep tracking changes after restarts, use Redis, LevelDB, or SQLite storages.

        Args:
            game (Game): The game to track.
            storage (StorageBaseClass, optional): The storage to use. New InMemoryStorage will be created if not provided.
            ignore_old_notices (bool, optional): Whether to ignore old notices on first initialization. Defaults to True.
            tracker_id (Union[str, int], optional): The tracker ID used to distinguish multiple trackers by the same game. Defaults to 1.
        """
        
        self._game : Game = game
        self._gzapi : GZAPI = game._gzapi
        self._storage : StorageBaseClass = None
        
        if storage is None:
            self._storage = InMemoryStorage()
        else:
            self._storage = storage
        self._lock = Lock()
        self._tracker_id = tracker_id
        self._lnid_key = f'NoticesTracker{tracker_id}-Game{self._game.id}-LNID'
        self._nlist_key = f'NoticesTracker{tracker_id}-Game{self._game.id}-NLIST'
        if ignore_old_notices and self._storage.get(self._lnid_key) is None:
            self.get_updates()
    
    @property
    def last_nid(self) -> int:
        """
        The last notice ID that was retrieved.

        The last notice ID that was retrieved the last time get_updates() or get_new() was called.
        If get_updates() or get_new() has not been called yet, this property will be 0 or the actual last notice ID retrieved on initialization, depending on ignore_old_notices.
        """
        notice_id = self._storage.get(self._lnid_key)
        return notice_id if notice_id is not None else 0
    
    @last_nid.setter
    def last_nid(self, notice_id: int):
        self._storage.set(self._lnid_key, notice_id)
    
    @property
    def _old_notices(self) -> List[Notice]:
        old_notices = self._storage.get(self._nlist_key)
        if old_notices is None:
            old_notices = []
        return [Notice.from_dict(notice) for notice in old_notices]
    
    @_old_notices.setter
    def _old_notices(self, notices: List[Notice]):
        self._storage.set(self._nlist_key, [asdict(notice) for notice in notices])
    
    def get_new(self, limit: Optional[int]=None) -> List[Notice]:
        """
        Get a list of new notices since the last call of get_updates()/get_new() (or start of the program).
        Note: This method doesn't affect get_updates() results except new notices.

        Args:
            limit (int, optional): The maximum number of notices to return. Defaults to None.

        Returns:
            List: A list of Notice objects.
        """
        with self._lock:
            lnid = self.last_nid
            new_notices = list(filter(lambda notice: notice.id > lnid, self._game.notices()))
            if limit is not None:
                new_notices = new_notices[:limit]
            if len(new_notices) != 0:
                self.last_nid = new_notices[-1].id  #* not using max() cause filter() should preserve the order
            return new_notices
    
    #! more testing and review needed
    def get_updates(self) -> List[NoticeUpdate]:
        with self._lock:
            new_notices = self._game.notices()
            old_notices = self._old_notices
            new_as_dict = {notice.id: notice for notice in new_notices}
            old_as_dict = {notice.id: notice for notice in old_notices}
            updates = []
            diff = utils.list_diff(new_as_dict.keys(), old_as_dict.keys())
            for common in diff.common:
                if new_as_dict[common] != old_as_dict[common]:
                    updates.append(NoticeUpdate(
                        update_type=NoticeUpdateTypes.edited,
                        new_notice=new_as_dict[common],
                        old_notice=old_as_dict[common],
                    ))
            for unique1 in diff.unique1:
                updates.append(NoticeUpdate(
                    update_type=NoticeUpdateTypes.new,
                    new_notice=new_as_dict[unique1],
                    old_notice=None,
                ))
            for unique2 in diff.unique2:
                updates.append(NoticeUpdate(
                    update_type=NoticeUpdateTypes.deleted,
                    new_notice=None,
                    old_notice=old_as_dict[unique2],
                ))
            updates.sort(key=lambda update: update.id)
            if len(new_notices) != 0:
                self.last_nid = new_notices[-1].id
            self._old_notices = new_notices
            return updates