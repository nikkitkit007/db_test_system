import gzip
import logging
import os
import shutil
from logging.handlers import RotatingFileHandler

import structlog
from structlog.contextvars import merge_contextvars
from structlog.stdlib import ProcessorFormatter

from src.config.config import settings


class GZipRotator:
    @staticmethod
    def namer(name):
        return name + ".gz"

    @staticmethod
    def rotator(source, dest) -> None:
        with open(source, "rb") as f_in, gzip.open(dest, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove(source)


def setup_logging() -> None:
    logging.basicConfig(level=settings.LogLevel, format=settings.LogFormat)

    handler = RotatingFileHandler("log.log",
                                  maxBytes=settings.LogFileSizeMB * 1024 * 1024,
                                  backupCount=settings.LogFileCount)
    handler.setFormatter(logging.Formatter(settings.LogFormat))
    handler.namer = GZipRotator.namer
    handler.rotator = GZipRotator.rotator

    pre_chain = [
        merge_contextvars,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=True),
        structlog.processors.add_log_level,
        structlog.processors.CallsiteParameterAdder({
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        }),
    ]

    structlog.configure(
        processors=[*pre_chain, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handler.setFormatter(ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=pre_chain,
    ))

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.LogLevel)


setup_logging()


def get_logger(name):
    return structlog.get_logger(name)
