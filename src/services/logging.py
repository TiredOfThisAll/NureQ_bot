from datetime import datetime


class LoggingLevel:
    INFO = "INFO"  # for general information
    WARN = "WARN"  # for potential errors or errors that can be recovered from
    ERROR = "ERROR"  # for errors that cannot be recovered from


def get_formatted_log(level, message):
    return f"{level} at {datetime.utcnow()} UTC: {message}\n"


class ConsoleLogger:
    def log(self, level, message):
        print(get_formatted_log(level, message))


class FileLogger:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path

    def log(self, level, message):
        with open(self.log_file_path, "a") as log_file:
            log_file.write(get_formatted_log(level, message))


class CompositeLogger:
    def __init__(self, loggers):
        self.loggers = loggers

    def log(self, level, message):
        for logger in self.loggers:
            logger.log(level, message)
