"""
Settings persistence for Pathfinder.
Saves and loads user parameters to/from JSON file.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from pathfinder.core.models import Parameters

logger = logging.getLogger(__name__)

# Settings file location in user's home directory
SETTINGS_DIR = Path.home() / ".pathfinder"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


def get_settings_path() -> Path:
    """Get the path to the settings file, creating directory if needed"""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    return SETTINGS_FILE


def save_parameters(parameters: Parameters) -> bool:
    """
    Save Parameters to JSON file.

    Args:
        parameters: Parameters object to save

    Returns:
        True if successful, False otherwise
    """
    try:
        settings_path = get_settings_path()

        # Convert Parameters (Pydantic model) to dict
        params_dict = parameters.model_dump()

        # Save to JSON with pretty formatting
        with open(settings_path, 'w') as f:
            json.dump(params_dict, f, indent=2)

        logger.info(f"Settings saved to {settings_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        return False


def load_parameters() -> Optional[Parameters]:
    """
    Load Parameters from JSON file.

    Returns:
        Parameters object if successful, None if file doesn't exist or load fails
    """
    try:
        settings_path = get_settings_path()

        if not settings_path.exists():
            logger.info("No saved settings found, will use defaults")
            return None

        # Load JSON
        with open(settings_path, 'r') as f:
            params_dict = json.load(f)

        # Create Parameters object from dict
        parameters = Parameters(**params_dict)

        logger.info(f"Settings loaded from {settings_path}: {parameters.name}")
        return parameters

    except Exception as e:
        logger.warning(f"Failed to load settings (will use defaults): {e}")
        return None


def reset_settings() -> bool:
    """
    Delete saved settings file to reset to defaults.

    Returns:
        True if successful or file didn't exist, False on error
    """
    try:
        settings_path = get_settings_path()

        if settings_path.exists():
            settings_path.unlink()
            logger.info("Settings file deleted, will use defaults on next load")
        else:
            logger.info("No settings file to delete")

        return True

    except Exception as e:
        logger.error(f"Failed to delete settings file: {e}")
        return False


def get_settings_info() -> dict:
    """
    Get information about the settings file.

    Returns:
        Dictionary with settings file info (path, exists, size, etc.)
    """
    settings_path = get_settings_path()

    info = {
        'path': str(settings_path),
        'exists': settings_path.exists(),
        'directory': str(SETTINGS_DIR),
    }

    if settings_path.exists():
        info['size_bytes'] = settings_path.stat().st_size
        info['modified'] = settings_path.stat().st_mtime

    return info
