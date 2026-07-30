import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = Path(__file__).parent / "db_config.json"
DEFAULT_DB = str(Path(__file__).parent / "chinook.sqlite")

def is_postgres() -> bool:
    return bool(os.getenv("DATABASE_URL"))

def get_database_url() -> str:
    return os.getenv("DATABASE_URL")

def get_db_path() -> str:
    if not CONFIG_PATH.exists():
        return DEFAULT_DB
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
            return data.get("db_path", DEFAULT_DB)
    except Exception:
        return DEFAULT_DB

def set_db_path(path: str):
    if not Path(path).exists():
        raise FileNotFoundError(f"Database file not found at {path}")
    with open(CONFIG_PATH, "w") as f:
        json.dump({"db_path": str(path)}, f)
