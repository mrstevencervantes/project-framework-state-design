"""Create logger which can be passed to other modules."""

import logging.config
from pathlib import Path

import yaml
from colorlog import ColoredFormatter


def logger_setup(json_data: dict):
    """Create logger which can be passed to other modules."""
    
    # Create the 'Log' folder if it doesn't exist
    log_folder = Path.joinpath(json_data.get("work_dir"), json_data.get("log_path"))
    log_folder.mkdir(exist_ok=True)

    # Read in logger config yaml file with safe load
    with open(json_data.pop("logger_path"), 'r') as f:
        config_dict = yaml.safe_load(f)

    # Update logger file path to include the working directory
    log_file_path = Path.joinpath(json_data.get("work_dir"), config_dict["handlers"]["file"]["filename"])

    # Create the debugging_file.log if it doesn't exist
    if not log_file_path.exists():
        with open(log_file_path, 'w') as file:
            pass

    # Update logger configuration with the new file path
    config_dict["handlers"]["file"]["filename"] = log_file_path

    # Set up console logging based on config_json, set False if not found
    if json_data.pop("logging_colors", False):
        config_dict['handlers']['console']['formatter'] = 'colorFormatter'

        # Create color formatter for console output
        color_formatter = ColoredFormatter(
            config_dict["formatters"]['colorFormatter']['format'],
            log_colors=config_dict["formatters"]['colorFormatter']['log_colors'],
            reset=True,
        )

        # Update console handler with the color formatter
        config_dict['handlers']['console']['formatter'] = 'color'
        config_dict['formatters']['color'] = {
            '()': color_formatter.__class__,
            'format': color_formatter._fmt,
            'log_colors': color_formatter.log_colors
        }
    else:
        config_dict['handlers']['console']['formatter'] = 'consoleFormatter'

    # create logger
    logging.config.dictConfig(config_dict)
    logger = logging.getLogger("main")
    return logger
