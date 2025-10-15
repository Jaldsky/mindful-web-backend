import logging

from .manager import ManagerAsync, ManagerSync
from ...config import DATABASE_ASYNC_URL, DATABASE_SYNC_URL


class Provider:
    def __init__(self, logger=logging.getLogger(__name__)) -> None:
        self.logger = logger
        self._sync_manager: ManagerSync | None = None
        self._async_manager: ManagerAsync | None = None

    @property
    def sync_manager(self) -> ManagerSync:
        if self._sync_manager is None:
            self._sync_manager = ManagerSync(logger=self.logger, database_url=DATABASE_SYNC_URL)
        return self._sync_manager

    @property
    def async_manager(self) -> ManagerAsync:
        if self._async_manager is None:
            self._async_manager = ManagerAsync(logger=self.logger, database_url=DATABASE_ASYNC_URL)
        return self._async_manager
