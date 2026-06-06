from __future__ import annotations

import logging
import time
from contextlib import contextmanager


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


@contextmanager
def timed_step(logger: logging.Logger, step_name: str):
    started_at = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - started_at
        logger.info("step=%s duration_sec=%.4f", step_name, elapsed)
