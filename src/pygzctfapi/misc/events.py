from enum import StrEnum


class NoticeEvents(StrEnum):
    NEW = 'notice.new'
    EDITED = 'notice.edited'
    DELETED = 'notice.deleted'
