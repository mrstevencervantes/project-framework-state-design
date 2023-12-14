"""Main file to run script. Please see README.md and config file for more info."""

import logging

# Setup main logger
logger = logging.getLogger("main")


def main(data: dict) -> None:
    """Main function to be run."""

    logger.debug(f"Starting main function.")

    logger.critical(f"Replace this with the actual function you want to run.")

    logger.debug(f"Main function completed.")
    return True
