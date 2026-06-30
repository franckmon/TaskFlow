from enum import Enum


class TaskStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class TaskSortField(str, Enum):
    CREATED_AT = "created_at"
    PRIORITY = "priority"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 1000
