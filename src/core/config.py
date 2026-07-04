"""Configuration loader and management"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


class ConfigLoader:
    """Load and manage application configuration"""

    def __init__(self, config_path: str = "config.yaml", env_path: str = ".env"):
        """Initialize config loader"""
        self.config_path = Path(config_path)
        self.env_path = Path(env_path)
        self._config: Dict[str, Any] = {}

        if self.env_path.exists():
            load_dotenv(self.env_path)

        if self.config_path.exists():
            self._load_yaml()
        else:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

    def _load_yaml(self) -> None:
        """Load YAML configuration file"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}

        self._config = self._replace_env_vars(self._config)

    def _replace_env_vars(self, obj: Any) -> Any:
        """Recursively replace ${VAR} with environment variables"""
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            if obj.startswith("${") and obj.endswith("}"):
                var_name = obj[2:-1]
                return os.getenv(var_name, obj)
            return obj
        return obj

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key"""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self._config.get(section, {})

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access"""
        return self.get(key)


_config_instance: ConfigLoader | None = None


def get_config() -> ConfigLoader:
    """Get or create global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance


def init_config(config_path: str = "config.yaml", env_path: str = ".env") -> ConfigLoader:
    """Initialize config with custom paths"""
    global _config_instance
    _config_instance = ConfigLoader(config_path, env_path)
    return _config_instance
