import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# Load the assigned .env layer, without overwriting real OS environment variables.
load_dotenv(BASE_DIR / ".env", override=False)

def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}

def coerce(key: str, value: Any) -> Any:
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return as_bool(value)
    return str(value)

def effective_config(overrides: list[str]) -> dict[str, Any]:
    config = DEFAULTS.copy()

    # Layer 2: environment-specific YAML.
    env_name = os.getenv("APP_ENV", "development")
    yaml_path = BASE_DIR / f"config.{env_name}.yaml"
    if yaml_path.exists():
        with yaml_path.open("r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
        for key, value in yaml_config.items():
            config[key.lower()] = value

    # Layer 3: values explicitly present in the .env file.
    # Parse the file separately so OS variables do not accidentally become .env values.
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        from dotenv import dotenv_values
        env_file = dotenv_values(env_path)
        mapping = {
            "APP_PORT": "port",
            "NUM_WORKERS": "workers",
            "APP_WORKERS": "workers",
            "APP_DEBUG": "debug",
            "APP_LOG_LEVEL": "log_level",
            "APP_API_KEY": "api_key",
        }
        for env_key, key in mapping.items():
            if env_file.get(env_key) is not None:
                config[key] = env_file[env_key]

    # Layer 4: OS-level environment variables with APP_* prefix.
    os_mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }
    for env_key, key in os_mapping.items():
        if env_key in os.environ:
            config[key] = os.environ[env_key]

    # Highest precedence: repeated ?set=key=value query parameters.
    for item in overrides:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip().lower()
        if key in config:
            config[key] = value

    # Normalize types and never expose the secret.
    result = {
        "port": coerce("port", config["port"]),
        "workers": coerce("workers", config["workers"]),
        "debug": coerce("debug", config["debug"]),
        "log_level": coerce("log_level", config["log_level"]),
        "api_key": "****",
    }
    return result

app = FastAPI(title="Layered Configuration API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Config service is running", "endpoint": "/effective-config"}

@app.get("/effective-config")
def get_effective_config(set: list[str] = Query(default=[])):
    return effective_config(set)
