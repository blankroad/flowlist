from pathlib import Path

APP_NAME = "FlowList"
APP_VERSION = "0.3.0"

# Data directory
DATA_DIR = Path.home() / ".flowlist"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "flowlist.db"

# Server
HOST = "127.0.0.1"
PORT = 5000

# GTD Schedules
SCHEDULE_INBOX = "inbox"
SCHEDULE_TODAY = "today"
SCHEDULE_UPCOMING = "upcoming"
SCHEDULE_ANYTIME = "anytime"
SCHEDULE_SOMEDAY = "someday"

# Task statuses
STATUS_INBOX = "inbox"
STATUS_ACTIVE = "active"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"
