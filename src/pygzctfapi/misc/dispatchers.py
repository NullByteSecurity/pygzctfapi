import threading
import time
from typing import TYPE_CHECKING, List, Union
from pygzctfapi import exceptions
from pygzctfapi.misc.routers import BaseRouter
from pygzctfapi.misc.trackers import DispatchableTracker

if TYPE_CHECKING:
    pass

class BaseDispatcher:
    _is_running: bool = False
    _thread : threading.Thread
    
    def __init__(self):
        pass

    def start(self):
        self._raise_if_running()
        self._is_running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.start()
    
    def run(self):
        self.start()

    def stop(self):
        self._is_running = False
        self._thread.join()

    def _run(self):
        raise NotImplementedError
    
    def _raise_if_running(self) -> bool:
        if self._is_running:
            raise exceptions.DispatcherIsRunningError()
    
    

class TrackerDispatcher(BaseDispatcher):
    def __init__(self, routers: Union['BaseRouter', List['BaseRouter']] = None, trackers: Union['DispatchableTracker', List['DispatchableTracker']] = None, polling_interval: int=10, errors_treshold: int=10):
        if routers is None:
            routers = []
        if trackers is None:
            trackers = []
        if isinstance(routers, BaseRouter):
            routers = [routers]
        elif isinstance(routers, List):
            for router in routers:
                if not isinstance(router, BaseRouter):
                    raise TypeError(f"Router {router} is not a valid router.")
        else:
            raise TypeError(f"Router {routers} is not a valid router.")
        if isinstance(trackers, DispatchableTracker):
            trackers = [trackers]
        elif isinstance(trackers, List):
            for tracker in trackers:
                if not isinstance(tracker, DispatchableTracker):
                    raise TypeError(f"Tracker {tracker} is not a valid tracker.")
        else:
            raise TypeError(f"Tracker {trackers} is not a valid tracker.")
        self._trackers = trackers
        self._routers = routers
        self._polling_interval = polling_interval
        self._errors_treshold = errors_treshold
        self._errors = 0
        self._consecutive_errors = 0
    
    def _raise_if_no_routers(self) -> bool:
        if len(self._routers) == 0:
            raise exceptions.NoRoutersError()
    
    def _raise_if_no_trackers(self) -> bool:
        if len(self._trackers) == 0:
            raise exceptions.NoTrackersError()
    
    def add_tracker(self, tracker: 'DispatchableTracker'):
        self._raise_if_running()
        if tracker not in self._trackers:
            if isinstance(tracker, DispatchableTracker):
                self._trackers.append(tracker)
            else:
                raise TypeError(f"Tracker {tracker} is not a valid tracker.")
        else:
            raise exceptions.TrackerAlreadyRegisteredError(tracker=tracker)
    
    def remove_tracker(self, tracker: 'DispatchableTracker'):
        self._raise_if_running()
        if tracker in self._trackers:
            self._trackers.remove(tracker)
        else:
            raise exceptions.TrackerNotRegisteredError(tracker=tracker)
    
    def add_router(self, router: 'BaseRouter'):
        self._raise_if_running()
        if router not in self._routers:
            if isinstance(router, BaseRouter):
                self._routers.append(router)
            else:
                raise TypeError(f"Router {router} is not a valid router.")
        else:
            raise exceptions.RouterAlreadyRegisteredError(router=router)
    
    def remove_router(self, router: 'BaseRouter'):
        self._raise_if_running()
        if router in self._routers:
            self._routers.remove(router)
        else:
            raise exceptions.RouterNotRegisteredError(router=router)

    def start(self):
        self._raise_if_no_routers()
        self._raise_if_no_trackers()
        return super().start()

    @property
    def polling_interval(self) -> int:
        """
        The time interval in seconds to wait between requests.
        This interval is used by the dispatcher to determine how often to poll from the tracker.
        The default value is 10 seconds.
        """
        return self._polling_interval
    
    @polling_interval.setter
    def polling_interval(self, polling_interval: int):
        self._polling_interval = polling_interval
    
    @property
    def errors_treshold(self) -> int:
        """
        The maximum number of consecutive errors before raising an exception and stopping the dispatcher.
        This value is used by the dispatcher to determine how many consecutive errors it should tolerate.
        The default value is 10 errors.
        """
        return self._errors_treshold
    
    @errors_treshold.setter
    def errors_treshold(self, errors_treshold: int):
        self._errors_treshold = errors_treshold
    
    def _run(self):
        while self._is_running:
            try:
                for tracker in self._trackers:
                    events = tracker.dispatch_updates()
                    for event in events:
                        for router in self._routers:
                            if event.event in router.events:
                                router.trigger_event(event)
                self._consecutive_errors = 0
                time.sleep(self._polling_interval)
            except exceptions.GZException as e:
                self._errors += 1
                self._consecutive_errors += 1
                if self._consecutive_errors >= self._errors_treshold:
                    self._is_running = False
                    raise e
                time.sleep(self._polling_interval)