from __future__ import annotations

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Mapping

DEFAULT_COLORS = {
    "DEBUG": "\033[94m",
    "INFO": "\033[90m",
    "WARNING": "\033[93m",
    "ERROR": "\033[1;91m",
    "CRITICAL": "\033[38;5;196m",
}
RESET_COLOR = "\033[0m"
DEFAULT_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _resolve_log_level(log_level: int | str) -> int:
    """将字符串或整数形式的日志级别统一转换为 logging 可识别的整数值。"""
    if isinstance(log_level, int):
        return log_level

    normalized_level = log_level.strip().upper()
    level_mapping = logging.getLevelNamesMapping()

    if normalized_level not in level_mapping:
        raise ValueError(
            f"不支持的日志级别: {log_level!r}。"
            "可选值示例: DEBUG、INFO、WARNING、ERROR、CRITICAL。"
        )

    return level_mapping[normalized_level]


def _resolve_logger_name(name: str | None, stacklevel: int = 2) -> str:
    """自动推断调用方模块名，允许外部省略 __name__。"""
    if name:
        return name

    try:
        frame = sys._getframe(stacklevel)
    except ValueError:
        return "__main__"

    return frame.f_globals.get("__name__", "__main__")


class ColoredFormatter(logging.Formatter):
    """给控制台日志添加 ANSI 颜色。"""

    def __init__(
        self,
        colors: Mapping[str, str],
        fmt: str | None = None,
        datefmt: str | None = None,
    ) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.colors = dict(colors)

    def format(self, record: logging.LogRecord) -> str:
        log_message = super().format(record)
        color = self.colors.get(record.levelname, "")
        return f"{color}{log_message}{RESET_COLOR}" if color else log_message


class LOGGER:
    """彩色日志封装，支持控制台输出和按天切分文件日志。

    该类本身可以直接当作 logger 使用，也可以通过 get_logger()
    取到底层的原生 logging.Logger。
    """

    def __init__(
        self,
        name: str | None = None,
        log_level: int | str = logging.DEBUG,
        save: bool = False,
        file_name: str | None = None,
        colors: Mapping[str, str] | None = None,
        log_dir: str | os.PathLike[str] | None = None,
        fmt: str = DEFAULT_FORMAT,
        datefmt: str = DEFAULT_DATE_FORMAT,
    ) -> None:
        """初始化日志器。

        参数:
            name: 日志器名称；不传时自动使用调用方模块名。
            log_level: 日志级别，支持整数或字符串，如 DEBUG、INFO。
            save: 是否写入文件。
            file_name: 日志文件名，不含扩展名。
            colors: 自定义颜色映射。
            log_dir: 日志目录，默认当前目录下的 logs。
            fmt: 日志格式。
            datefmt: 时间格式。
        """
        self.colors = dict(DEFAULT_COLORS)
        if colors:
            self.colors.update(colors)

        resolved_log_level = _resolve_log_level(log_level)
        resolved_name = _resolve_logger_name(name=name, stacklevel=2)
        self.logger = logging.getLogger(resolved_name)
        self.logger.setLevel(resolved_log_level)
        self.logger.propagate = False

        self._setup_console_handler(
            log_level=resolved_log_level,
            fmt=fmt,
            datefmt=datefmt,
        )

        if save:
            self._setup_file_handler(
                log_level=resolved_log_level,
                file_name=file_name,
                log_dir=log_dir,
                fmt=fmt,
                datefmt=datefmt,
            )

    def _find_handler(self, handler_type: str) -> logging.Handler | None:
        """查找当前 logger 上由本库创建的 handler。"""
        for handler in self.logger.handlers:
            if getattr(handler, "_dlz_logger_handler_type", None) == handler_type:
                return handler
        return None

    def _setup_console_handler(self, log_level: int, fmt: str, datefmt: str) -> None:
        """配置或复用控制台 handler，避免重复输出。"""
        console_handler = self._find_handler("console")
        formatter = ColoredFormatter(self.colors, fmt=fmt, datefmt=datefmt)

        if console_handler is None:
            console_handler = logging.StreamHandler()
            console_handler._dlz_logger_handler_type = "console"  # type: ignore[attr-defined]
            self.logger.addHandler(console_handler)

        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)

    def _setup_file_handler(
        self,
        log_level: int,
        file_name: str | None,
        log_dir: str | os.PathLike[str] | None,
        fmt: str,
        datefmt: str,
    ) -> None:
        """配置按天轮转的文件日志。"""
        target_path = self._build_log_path(file_name=file_name, log_dir=log_dir)
        file_handler = self._find_handler("file")

        if (
            file_handler is not None
            and getattr(file_handler, "baseFilename", None) != str(target_path)
        ):
            # 同一个 logger 只保留一个文件 handler，后一次配置覆盖前一次。
            self.logger.removeHandler(file_handler)
            file_handler.close()
            file_handler = None

        if file_handler is None:
            file_handler = TimedRotatingFileHandler(
                filename=target_path,
                when="midnight",
                interval=1,
                backupCount=0,
                encoding="utf-8",
            )
            file_handler._dlz_logger_handler_type = "file"  # type: ignore[attr-defined]
            file_handler.suffix = "%Y-%m-%d.log"
            self.logger.addHandler(file_handler)

        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    @staticmethod
    def _build_log_path(
        file_name: str | None,
        log_dir: str | os.PathLike[str] | None,
    ) -> Path:
        """生成日志文件完整路径。"""
        resolved_file_name = file_name or "main"
        resolved_log_dir = Path(log_dir) if log_dir else Path.cwd() / "logs"
        resolved_log_dir.mkdir(parents=True, exist_ok=True)
        return resolved_log_dir / f"{resolved_file_name}.log"

    def debug(self, msg: object, *args: object, **kwargs: object) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: object, *args: object, **kwargs: object) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: object, *args: object, **kwargs: object) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: object, *args: object, **kwargs: object) -> None:
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: object, *args: object, **kwargs: object) -> None:
        self.logger.critical(msg, *args, **kwargs)

    def __getattr__(self, item: str) -> object:
        """将未显式实现的属性和方法转发到底层 logger。"""
        return getattr(self.logger, item)

    def get_logger(self) -> logging.Logger:
        """返回原生 logging.Logger，方便无缝接入现有代码。"""
        return self.logger


def get_logger(
    name: str | None = None,
    log_level: int | str = logging.DEBUG,
    save: bool = False,
    file_name: str | None = None,
    colors: Mapping[str, str] | None = None,
    log_dir: str | os.PathLike[str] | None = None,
    fmt: str = DEFAULT_FORMAT,
    datefmt: str = DEFAULT_DATE_FORMAT,
) -> logging.Logger:
    """函数式入口，推荐直接使用这个接口。"""
    resolved_name = _resolve_logger_name(name=name, stacklevel=2)
    return LOGGER(
        name=resolved_name,
        log_level=log_level,
        save=save,
        file_name=file_name,
        colors=colors,
        log_dir=log_dir,
        fmt=fmt,
        datefmt=datefmt,
    ).get_logger()
