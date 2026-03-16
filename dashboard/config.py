import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

# MongoDB connection
MONGO_USER = os.getenv("MONGO_USER", "microservices")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DB", "analytics")

MONGO_URI = os.getenv(
    "MONGO_URI",
    f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}"
    f"/{MONGO_DB}?authSource=admin&retryWrites=false",
)

# TLS certificate for AWS DocumentDB
TLS_CA_FILE = str(_project_root / "certs" / "global-bundle.pem")

# Agent name constants
AGENTS = {
    "Tommy": "on-call-guardian",
    "Partnerships": "partnerships-agent",
}

# Cache TTL in seconds (1 hour)
CACHE_TTL = 3600
