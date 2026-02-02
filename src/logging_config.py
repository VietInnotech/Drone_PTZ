from __future__ import annotations

import contextlib
import logging
import sys
from pathlib import Path

from loguru import logger

from src.settings import Settings, load_settings


_KNOWN_LEVELS = {
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
}


class InterceptHandler(logging.Handler):
    """Redirect stdlib logging records to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _normalize_level(level: str | None) -> str:
    if not level:
        return "INFO"
    normalized = level.strip().upper()
    if normalized in _KNOWN_LEVELS:
        return normalized
    return "INFO"


def setup_logging(
    settings: Settings | None = None,
    *,
    config_path: Path | None = None,
    env_file: Path | None = None,
) -> Settings:
    """Configure Loguru (and bridge stdlib logging) using config settings."""
    if settings is None:
        settings = load_settings(config_path=config_path, env_file=env_file)

    log_cfg = settings.logging
    level = _normalize_level(log_cfg.log_level)

    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format=log_cfg.log_format,
        enqueue=log_cfg.log_enqueue,
        backtrace=log_cfg.log_backtrace,
        diagnose=log_cfg.log_diagnose,
    )

    if log_cfg.write_log_file and log_cfg.log_file:
        log_path = Path(log_cfg.log_file)
        if not log_path.is_absolute() and config_path is not None:
            log_path = Path(config_path).parent / log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if log_cfg.reset_log_on_start and log_path.exists():
            with contextlib.suppress(OSError):
                log_path.unlink()
        logger.add(
            str(log_path),
            level=level,
            format=log_cfg.log_format,
            rotation=log_cfg.log_rotation,
            retention=log_cfg.log_retention,
            enqueue=log_cfg.log_enqueue,
            backtrace=log_cfg.log_backtrace,
            diagnose=log_cfg.log_diagnose,
        )

    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.getLevelName(level))
    for name in list(logging.root.manager.loggerDict.keys()):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    return settings
