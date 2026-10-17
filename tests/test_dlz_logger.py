import logging
import tempfile
import unittest
from pathlib import Path

from dlz_logger import LOGGER, get_logger


class TestDlzLogger(unittest.TestCase):
    def test_logger_class_can_be_used_directly(self) -> None:
        logger = LOGGER(name="test.direct", log_level=logging.INFO)
        logger.info("direct logger works")

        self.assertEqual(logger.name, "test.direct")
        self.assertEqual(logger.level, logging.INFO)

    def test_logger_class_supports_string_log_level(self) -> None:
        logger = LOGGER(name="test.string.level", log_level="debug")
        self.assertEqual(logger.level, logging.DEBUG)

    def test_function_api_supports_string_log_level(self) -> None:
        logger = get_logger(name="test.function.string.level", log_level="WARNING")
        self.assertEqual(logger.level, logging.WARNING)

    def test_invalid_string_log_level_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            LOGGER(name="test.invalid.level", log_level="NOT_A_LEVEL")

    def test_logger_class_can_infer_module_name(self) -> None:
        logger = LOGGER().get_logger()
        self.assertEqual(logger.name, __name__)

    def test_function_api_can_infer_module_name(self) -> None:
        logger = get_logger()
        self.assertEqual(logger.name, __name__)

    def test_file_handler_can_be_created(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = get_logger(
                name="test.file",
                log_level=logging.INFO,
                save=True,
                file_name="sample",
                log_dir=temp_dir,
            )
            logger.info("hello file logger")

            for handler in logger.handlers:
                handler.flush()

            self.assertTrue((Path(temp_dir) / "sample.log").exists())

            for handler in list(logger.handlers):
                if getattr(handler, "_dlz_logger_handler_type", None) == "file":
                    logger.removeHandler(handler)
                    handler.close()

    def test_console_handler_will_not_duplicate(self) -> None:
        logger = get_logger(name="test.console")
        logger = get_logger(name="test.console")

        console_handlers = [
            handler
            for handler in logger.handlers
            if getattr(handler, "_dlz_logger_handler_type", None) == "console"
        ]
        self.assertEqual(len(console_handlers), 1)

    def test_custom_levels_are_registered(self) -> None:
        from dlz_logger import (
            AUDIT,
            ANNOUNCEMENT,
            FAIL,
            METRIC,
            NOTICE,
            RETRY,
            SUCCESS,
            TRACE,
        )

        self.assertEqual(logging.getLevelName(TRACE), "TRACE")
        self.assertEqual(logging.getLevelName(NOTICE), "NOTICE")
        self.assertEqual(logging.getLevelName(SUCCESS), "SUCCESS")
        self.assertEqual(logging.getLevelName(RETRY), "RETRY")
        self.assertEqual(logging.getLevelName(FAIL), "FAIL")
        self.assertEqual(logging.getLevelName(AUDIT), "AUDIT")
        self.assertEqual(logging.getLevelName(ANNOUNCEMENT), "ANNOUNCEMENT")
        self.assertEqual(logging.getLevelName(METRIC), "METRIC")

    def test_custom_level_ordering(self) -> None:
        import dlz_logger

        self.assertLess(dlz_logger.TRACE, logging.DEBUG)
        self.assertLess(logging.INFO, dlz_logger.NOTICE)
        self.assertLess(dlz_logger.NOTICE, dlz_logger.SUCCESS)
        self.assertLess(dlz_logger.SUCCESS, logging.WARNING)
        self.assertLess(logging.WARNING, dlz_logger.RETRY)
        self.assertLess(dlz_logger.RETRY, logging.ERROR)
        self.assertLess(logging.ERROR, dlz_logger.FAIL)
        self.assertLess(dlz_logger.FAIL, logging.CRITICAL)
        self.assertLess(logging.CRITICAL, dlz_logger.AUDIT)
        self.assertLess(dlz_logger.AUDIT, dlz_logger.ANNOUNCEMENT)
        self.assertLess(dlz_logger.ANNOUNCEMENT, dlz_logger.METRIC)

    def test_custom_levels_can_be_used_as_string_level(self) -> None:
        from dlz_logger import CUSTOM_LEVELS

        for level_name, level_value in CUSTOM_LEVELS.items():
            with self.subTest(level=level_name):
                logger = LOGGER(name=f"test.string.{level_name}", log_level=level_name)
                self.assertEqual(logger.level, level_value)

    def test_custom_level_methods_emit_records(self) -> None:
        # TRACE 数值最小，需把阈值设为 TRACE 才能捕获全部自定义级别。
        logger = get_logger(name="test.custom.emit", log_level="TRACE")

        records: list[logging.LogRecord] = []

        class _Collector(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        collector = _Collector()
        logger.addHandler(collector)

        try:
            logger.trace("very detailed")
            logger.success("all good")
            logger.retry("retrying request")
            logger.fail("something broke")
            logger.audit("user logged in")
            logger.announcement("big news")
            logger.metric("elapsed_ms=42")
        finally:
            logger.removeHandler(collector)

        emitted_levels = [record.levelname for record in records]
        self.assertEqual(
            emitted_levels,
            ["TRACE", "SUCCESS", "RETRY", "FAIL", "AUDIT", "ANNOUNCEMENT", "METRIC"],
        )

    def test_custom_levels_respect_threshold(self) -> None:
        logger = get_logger(name="test.custom.threshold", log_level="ERROR")

        records: list[logging.LogRecord] = []

        class _Collector(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        collector = _Collector()
        logger.addHandler(collector)

        try:
            logger.success("hidden: below ERROR threshold")
            logger.retry("hidden: below ERROR threshold")
            logger.error("shown")
            logger.metric("shown: above ERROR threshold")
            logger.announcement("shown: always passes threshold")
        finally:
            logger.removeHandler(collector)

        emitted_levels = [record.levelname for record in records]
        self.assertEqual(emitted_levels, ["ERROR", "METRIC", "ANNOUNCEMENT"])

    def test_trace_is_filtered_by_debug_threshold(self) -> None:
        logger = get_logger(name="test.trace.threshold", log_level=logging.DEBUG)

        records: list[logging.LogRecord] = []

        class _Collector(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        collector = _Collector()
        logger.addHandler(collector)

        try:
            logger.trace("hidden: below DEBUG threshold")
            logger.debug("shown")
        finally:
            logger.removeHandler(collector)

        emitted_levels = [record.levelname for record in records]
        self.assertEqual(emitted_levels, ["DEBUG"])

    def test_custom_level_colors_are_configurable(self) -> None:
        from dlz_logger.logger import ColoredFormatter, DEFAULT_COLORS

        formatter = ColoredFormatter(DEFAULT_COLORS, fmt="%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test.color",
            level=logging.WARNING,
            pathname=__file__,
            lineno=1,
            msg="colored",
            args=(),
            exc_info=None,
        )
        record.levelname = "FAIL"
        self.assertIn("\033[38;5;205m", formatter.format(record))


if __name__ == "__main__":
    unittest.main()
