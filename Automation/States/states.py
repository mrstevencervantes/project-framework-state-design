import csv
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Callable, Any

from Script.script import main
from Config.project_setup import ConfigSetup

# Setup main logger
logger = logging.getLogger("main")


class StateContext:
    pass


class State:
    """Base class for states."""
    def process(self, context: StateContext) -> None:
        pass


class InitializationState(State):
    """Initial state of the application."""
    def process(self, context: StateContext):
        
        config_data = context.retry(self.config_setup)
        
        if config_data:
            logger.info("Initialization successful.")
            context.transition_to(ProcessingState(config_data))
        else:
            logger.info("Initialization failed.")
            context.transition_to(EndState(config_data, False))

    def config_setup(self) -> dict:
        """Perform config setup for later use in the application."""
        logger.debug(f"Starting initialization...")
        config = ConfigSetup('Config/Config.json')
        config_data = config.setup_dict()
        return config_data


class ProcessingState(State):
    """State to run the application."""
    def __init__(self, config_data: dict) -> None:
        self.config_data = config_data

    def process(self, context: StateContext):

        success = context.retry(main, self.config_data)

        if success:
            logger.info("Processing successful.")
            context.transition_to(EndState(self.config_data, True))
        else:
            logger.error("Processing failed.")
            context.transition_to(EndState(self.config_data, False))


class EndState(State):
    """State to end the application and log run."""
    def __init__(self, config_data: dict=None, successful_run: bool=True) -> None:
        self.config_data = config_data
        self.successful_run = successful_run

    def process(self, context: StateContext):
        logger.info("Process ended.")
        # Perform cleanup or post-processing tasks here
        self.write_log()

    def write_log(self) -> None:
        """Write output of current run to log file."""

        # Declare variables
        SCRIPT_NAME = self.config_data.get("ScriptName", self.config_data.get("parent_dir").name)
        LOG_FILE_PATH = Path.joinpath(self.config_data.get("parent_dir"), self.config_data.get("LogFile"))
        HEADER_ROW = ["Script Name", "Date/Time Run", "Username", "Successful?"]

        # File does not exist, so create it and write the header row
        if not LOG_FILE_PATH.is_file():
            with open(LOG_FILE_PATH, mode='w', newline='') as log_file:
                log_file_writer = csv.writer(log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                log_file_writer.writerow(HEADER_ROW)

        # Append content to the CSV file
        with open(LOG_FILE_PATH, mode='a', newline='') as log_file:
            log_file_writer = csv.writer(log_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            log_file_writer.writerow([SCRIPT_NAME, datetime.now(), self.config_data.get("username"), str(self.successful_run)])


class ErrorState(State):
    """State for logging any errors that occur during the application run."""
    def __init__(self, config_data: dict, successful_run: bool, error: str=None) -> None:
        self.config_data = config_data
        self.successful_run = successful_run
        self.error = error

    def process(self, context: StateContext):
        logger.error(f"Error occurred in {context.previous_state.__class__.__name__}.")

        self.log_exception(Path.joinpath(self.config_data.get("parent_dir"), self.config_data.get("ErrorOutput")))

    def log_exception(self, filename: Path) -> None:
        """Write out exceptions to file path provided."""

        logger.info("Writing error to file.")
        try:
            with open(filename, "w") as f:
                f.write(f"{datetime.now()}\n")
                f.write(f"{str(self.error).__class__.__name__}\n{self.error}")
        except FileNotFoundError as e:
            logger.error(str(e))
        except Exception as e:
            logger.critical(f"An unexpected error occurred. {type(e).__name__} {str(e)} Please review logs. Unable to continue.")
        else:
            logger.info("Error writing completed.")


class StateContext:
    def __init__(self):
        self.max_retry_count = 3
        self.retry_count = 0
        self.sleep_time = 3
        self.state = None
        self.previous_state = None
        self.error_signaled = False

    def start(self):
        """Start the state machine with Initialization."""
        self.transition_to(InitializationState())

    def transition_to(self, state: State, config_data: dict=None, successful_run: bool=True, error_signaled: bool=False):
        """Transition to a new state. If an error is signaled, transition to ErrorState.
        
        Args:
            state (State): State to transition to.
            config_data (dict, optional): Data to pass to the state. Defaults to None.
            successful_run (bool, optional): Whether or not the run was successful. Defaults to True.
            error_signaled (bool, optional): Whether or not an error was signaled. Defaults to False.
        """
        self.retry_count = 0
        self.error_signaled = error_signaled
        self.previous_state = self.state
        self.config_data = config_data
        self.successful_run = successful_run

        if self.error_signaled and isinstance(state, ErrorState):
            # Handle direct transition to EndState when error is signaled
            self.state = state
            self.state.process(self)
            self.transition_to(EndState(config_data=self.config_data, successful_run=self.successful_run))  # Transition to EndState
        else:
            self.state = state
            self.state.process(self)

    def retry(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Retry a function if an error occurs."""
        # Pull counts from config file, else go with defaults
        if self.config_data:
            self.max_retry_count = self.config_data.get("RetryNumber")
            self.sleep_time = self.config_data.get("RetryDelay")

        logger.debug(f"Trying to run function {func.__name__} with the following arguments: {args}, {kwargs}.")
        while self.retry_count < self.max_retry_count:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.retry_count += 1
                if self.retry_count == self.max_retry_count:
                    logger.error(f"Failed to run function {func.__name__}. Maximum number of retries reached.")
                    logger.error(f"Error: {e}")
                    self.transition_to(ErrorState(self.config_data, False, e), self.config_data, False, True)
                else:
                    logger.warning(f"Attempt {self.retry_count} failed. Retrying in {self.sleep_time} seconds...")
                    time.sleep(self.sleep_time)
