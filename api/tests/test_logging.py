from app.logging_setup import setup_logging, timed_step
import logging


class TestSetupLogging:
    def test_sets_info_level(self):
        setup_logging()
        logger = logging.getLogger("app")
        assert logger.level <= logging.INFO


class TestTimedStep:
    def test_logs_duration(self, caplog):
        logger = logging.getLogger("test_timed")
        with caplog.at_level(logging.INFO, logger="test_timed"):
            with timed_step(logger, "test_step"):
                pass
        assert any("step=test_step" in r.message for r in caplog.records)

    def test_logs_on_exception(self, caplog):
        logger = logging.getLogger("test_timed_exc")
        try:
            with caplog.at_level(logging.INFO, logger="test_timed_exc"):
                with timed_step(logger, "failing_step"):
                    raise ValueError("boom")
        except ValueError:
            pass
        assert any("step=failing_step" in r.message for r in caplog.records)
