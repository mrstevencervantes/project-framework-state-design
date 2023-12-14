"""Convert JSON file into a dictionary that can be passed to other modules for later use."""

import json
import logging
from pathlib import Path

from jsonschema import validate
from jsonschema.exceptions import ValidationError


def config_json(json_path: str='Config/Config.json', schema_path: str='Config/config-schema.json') -> dict:
    """Read JSON file and create a dictionary."""

    # Build current working directory and file paths
    WORKING_DIR = create_working_directory()
    JSON_FILE = Path.joinpath(WORKING_DIR, json_path)
    SCHEMA_FILE = Path.joinpath(WORKING_DIR, schema_path)

    try:
        # Read in JSON file
        with open(JSON_FILE) as f:
            json_data = json.load(f)

        # Read in JSON schema
        with open(SCHEMA_FILE) as f:
            schema = json.load(f)
    except FileNotFoundError:
        raise

    # Validate JSON schema, raise exception if invalid
    try:
        validate(instance=json_data, schema=schema)
    except ValidationError:
        raise

    # Create file paths for later use
    CONFIG_FILE = Path.joinpath(WORKING_DIR, json_data.pop("config_path"))
    LOGGER_FILE = Path.joinpath(WORKING_DIR, json_data.pop("logger_path"))

    # Make sure all file paths are valid, raise exception if not
    if not CONFIG_FILE.is_file():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")
    
    if not LOGGER_FILE.is_file():
        raise FileNotFoundError(f"Logger config file not found: {LOGGER_FILE}")

    # Create file paths for later use
    json_data["config_path"] = CONFIG_FILE
    json_data["logger_path"] = LOGGER_FILE
    json_data["work_dir"] = WORKING_DIR
    json_data["parent_dir"] = WORKING_DIR.parent

    return json_data


def create_working_directory() -> Path:
    temp = []
    for part in Path.cwd().parts:
        temp.append(part)
        if part.lower() == "automation":
            break
    return Path("/".join(temp))


if __name__ == "__main__":
    json_data = config_json('Config/Config.json', 'Config/config-schema.json')
