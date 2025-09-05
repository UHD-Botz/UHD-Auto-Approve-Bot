import os

# Basic Bot Configs
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Admin & Logging
try:
    ADMIN = int(os.environ.get("ADMIN", "0"))
except ValueError:
    ADMIN = None

try:
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))
except ValueError:
    LOG_CHANNEL = None

# Bot Images
PICS = [x for x in os.environ.get("PICS", "").split() if x]

# DB Settings
DB_URI = os.environ.get("DB_URI", "")
DB_NAME = os.environ.get("DB_NAME", "AutoApprove")

# Modes
NEW_REQ_MODE = os.environ.get("NEW_REQ_MODE", "False").lower() == "true"
IS_FSUB = os.environ.get("IS_FSUB", "False").lower() == "true"

# Authorized Channels
try:
    AUTH_CHANNELS = list(
        map(int, os.environ.get("AUTH_CHANNEL", "").split())
    )
except ValueError:
    AUTH_CHANNELS = []
