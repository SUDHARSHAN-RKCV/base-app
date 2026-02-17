import os

MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"
class Config:
    VERSION = os.getenv("APP_VERSION", "0.0.0")