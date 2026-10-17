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


if __name__ == "__main__":
    unittest.main()
