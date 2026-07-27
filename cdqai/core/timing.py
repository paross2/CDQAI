from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def timed_step(logger: logging.Logger, step_name: str) -> Iterator[None]:
    logger.info("START: %s", step_name)
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info("END: %s | elapsed %.2f seconds", step_name, elapsed)
