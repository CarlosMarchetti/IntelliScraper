import logging
import sys
from typing import Optional

from intelliscraper.config import config


class LoggerManager:
    _loggers = {}

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        
        if logger.handlers:
            return logger

        logger.setLevel(config.log_level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        cls._loggers[name] = logger
        return logger


get_logger = LoggerManager.get_logger
