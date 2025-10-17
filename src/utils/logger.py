"""Logging utility for the Agent project.

This module provides a simple interface for setting up loggers with
color support and consistent formatting across the application.
"""

from __future__ import annotations

import logging
import sys

# colorlog 라이브러리 가용성 확인
try:
    import colorlog

    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Setup and configure a logger with color support.

    Creates a logger with the specified name and level, configured with
    colored output if colorlog is available, otherwise uses standard logging.

    Args:
        name: The name of the logger (typically __name__ from the calling module).
        level: The logging level as a string. Valid values are:
            "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".
            Defaults to "INFO".

    Returns:
        logging.Logger: Configured logger instance ready for use.

    Raises:
        ValueError: If an invalid logging level is provided.

    Example:
        >>> from src.utils.logger import setup_logger
        >>> logger = setup_logger(__name__)
        >>> logger.info("Application started")
        [2025-10-15 10:30:45] [INFO] [myapp] Application started

        >>> logger = setup_logger(__name__, level="DEBUG")
        >>> logger.debug("Debug information")
        [2025-10-15 10:30:45] [DEBUG] [myapp] Debug information
    """
    # 로깅 레벨 검증
    numeric_level = _get_numeric_level(level)

    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)

    # 기존 핸들러가 있으면 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()

    # 콘솔 핸들러 생성
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # 포매터 설정 (colorlog 가용 여부에 따라)
    if COLORLOG_AVAILABLE:
        formatter = _create_color_formatter()
    else:
        formatter = _create_standard_formatter()

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 상위 로거로 전파 방지 (중복 로그 방지)
    logger.propagate = False

    return logger


def _get_numeric_level(level: str) -> int:
    """Convert string level to numeric logging level.

    Args:
        level: The logging level as a string.

    Returns:
        int: Numeric logging level.

    Raises:
        ValueError: If the level string is invalid.
    """
    level_upper = level.upper()
    numeric_level = getattr(logging, level_upper, None)

    if not isinstance(numeric_level, int):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        raise ValueError(
            f"Invalid log level: {level}. Valid levels are: {', '.join(valid_levels)}"
        )

    return numeric_level


def _create_color_formatter() -> colorlog.ColoredFormatter:
    """Create a colored log formatter using colorlog.

    Returns:
        colorlog.ColoredFormatter: Configured colored formatter.
    """
    log_format = (
        "%(log_color)s[%(asctime)s] [%(levelname)s] [%(name)s]%(reset)s %(message)s"
    )

    date_format = "%Y-%m-%d %H:%M:%S"

    log_colors = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    }

    formatter = colorlog.ColoredFormatter(
        log_format,
        datefmt=date_format,
        log_colors=log_colors,
        reset=True,
        style="%",
    )

    return formatter


def _create_standard_formatter() -> logging.Formatter:
    """Create a standard log formatter without colors.

    Returns:
        logging.Formatter: Configured standard formatter.
    """
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(log_format, datefmt=date_format)

    return formatter


def get_logger(name: str) -> logging.Logger:
    """Get an existing logger by name.

    This is a convenience function to retrieve loggers that have already
    been set up with setup_logger().

    Args:
        name: The name of the logger to retrieve.

    Returns:
        logging.Logger: The logger instance.

    Example:
        >>> from src.utils.logger import setup_logger, get_logger
        >>> setup_logger("myapp")
        >>> logger = get_logger("myapp")
        >>> logger.info("Using retrieved logger")
    """
    return logging.getLogger(name)


# 모듈 레벨에서 기본 로거 설정 (선택적)
def configure_root_logger(level: str = "INFO") -> None:
    """Configure the root logger for the entire application.

    This should be called once at application startup to set up
    the default logging configuration.

    Args:
        level: The logging level for the root logger. Defaults to "INFO".

    Example:
        >>> from src.utils.logger import configure_root_logger
        >>> configure_root_logger("DEBUG")
    """
    setup_logger("", level=level)  # Empty name = root logger
