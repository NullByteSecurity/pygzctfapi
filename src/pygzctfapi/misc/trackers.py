from abc import abstractmethod, ABC
from dataclasses import asdict
from typing import Generator, List, Optional, Union
from pygzctfapi.misc.events import NoticeEvents
from pygzctfapi.misc.storages import InMemoryStorage
from pygzctfapi.misc.updates import BaseUpdate, NoticeUpdate
from pygzctfapi.models import Notice
from pygzctfapi import utils
from threading import Lock

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygzctfapi import GZAPI
    from pygzctfapi.misc.updates import BaseUpdate
    from pygzctfapi.misc.storages import StorageBaseClass
    from pygzctfapi.models import Game
    from pygzctfapi.misc.dispatchers import TrackerDispatcher


class BaseTracker(ABC):
    _gzapi: 'GZAPI'
    _storage: 'StorageBaseClass'
    _tracker_id: Union[str, int]
    
    @abstractmethod
    def get_updates(self) -> List['BaseUpdate']:
        raise NotImplementedError

class DispatchableTracker(BaseTracker, ABC):
    @abstractmethod
    def dispatch_updates(self) -> Generator[tuple[str, BaseUpdate], None, None]:
        raise NotImplementedError


class NoticeTracker(DispatchableTracker):
    dispatcher: Optional['TrackerDispatcher'] = None
    
    def __init__(self, game: 'Game', storage: 'StorageBaseClass'=None, ignore_old_notices: bool=True, tracker_id: Union[str, int]=1):
        """
        Initialize the NoticeTracker.
        
        NoticeTracker tracks notices changes in a game. It supports polling [and handlers based on polling (not yet)].
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
        self._lnid_key = f'NoticeTracker{tracker_id}-Game{self._game.id}-LNID'
        self._nlist_key = f'NoticeTracker{tracker_id}-Game{self._game.id}-NLIST'
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
        """
        Get a list of updates to notices since the last call of get_updates() (or start of the program).

        This method will return a list of NoticeUpdate objects, each representing a change to a notice.
        The list will be sorted by notice ID.

        The method will also update the internal state of the tracker, so that the next call will return updates since the last call.

        Returns:
            List[NoticeUpdate]: A list of NoticeUpdate objects.
        """
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
                        event=NoticeEvents.EDITED,
                        new_notice=new_as_dict[common],
                        old_notice=old_as_dict[common],
                    ))
            for unique1 in diff.unique1:
                updates.append(NoticeUpdate(
                    event=NoticeEvents.NEW,
                    new_notice=new_as_dict[unique1],
                    old_notice=None,
                ))
            for unique2 in diff.unique2:
                updates.append(NoticeUpdate(
                    event=NoticeEvents.DELETED,
                    new_notice=None,
                    old_notice=old_as_dict[unique2],
                ))
            updates.sort(key=lambda update: update.id)
            if len(new_notices) != 0:
                self.last_nid = new_notices[-1].id
            self._old_notices = new_notices
            return updates
    
    def dispatch_updates(self) -> Generator[tuple[str, NoticeUpdate], None, None]:
        """
        A generator that yields a tuple with event name and NoticeUpdate object.
        The generator will yield updates since the last call of dispatch_updates() or get_updates().

        The event name is the name of the event as string, and the NoticeUpdate object
        contains information about the update. The events are NoticeEvents.NEW, NoticeEvents.EDITED,
        and NoticeEvents.DELETED.

        The method will also update the internal state of the tracker, so that the next call will return
        updates since the last call.

        Yields:
            tuple: A tuple containing the event name and a NoticeUpdate object.
        """
        for update in self.get_updates():
            yield (NoticeEvents(update.event), update)
