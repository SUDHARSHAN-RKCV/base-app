import os

MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"
