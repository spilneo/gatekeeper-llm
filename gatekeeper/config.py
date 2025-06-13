# gatekeeper/config.py
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

CONFIG_DIR = Path.home() / ".config" / "gatekeeper"
CONFIG_FILE = CONFIG_DIR / "config.json"

def _get_default_config() -> Dict[str, Any]:
    """Returns the default configuration dictionary, sourcing from environment variables."""
    return {
        "base_model": "mlx-community/Phi-3-mini-4k-instruct-8bit",
        "last_fused_model_path": None, # Only stores the path for user convenience
        "teacher_api_key": os.getenv("OPENAI_API_KEY"),
        "teacher_base_url": os.getenv("OPENAI_BASE_URL"),
        "teacher_model": os.getenv("OPENAI_MODEL"),
    }

def ensure_config_dir_exists():
    """Ensures the configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def save_config(data: Dict[str, Any]):
    """Saves the configuration dictionary to the config file."""
    ensure_config_dir_exists()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_config() -> Dict[str, Any]:
    """Loads the configuration, creating a default if it doesn't exist."""
    ensure_config_dir_exists()
    default_config = _get_default_config()
    
    if not CONFIG_FILE.is_file():
        save_config(default_config)
        return default_config
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            current_env_config = {
                "teacher_api_key": os.getenv("OPENAI_API_KEY"),
                "teacher_base_url": os.getenv("OPENAI_BASE_URL"),
                "teacher_model": os.getenv("OPENAI_MODEL"),
            }
            # Prioritize env vars over saved config for teacher settings
            for key, val in current_env_config.items():
                if val is not None:
                    config_data[key] = val
            # Ensure old/new keys are synced with the default
            for key in default_config:
                if key not in config_data:
                    config_data[key] = default_config[key]
            return config_data
    except json.JSONDecodeError:
        save_config(default_config)
        return default_config

def get_last_model_path() -> Optional[str]:
    """Safely retrieves the last created model path from the config."""
    return load_config().get("last_fused_model_path")