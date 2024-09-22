from typing import Callable, Generator
from unittest.mock import patch

import pytest
import structlog
from _pytest.capture import CaptureFixture
from structlog.typing import WrappedLogger

import structlog_gcp

from . import fakes


@pytest.fixture
def mock_logger_env() -> Generator[None, None, None]:
    with (
        patch(
            "structlog.processors.CallsiteParameterAdder",
            side_effect=fakes.CallsiteParameterAdder,
        ),
        patch("structlog.processors.TimeStamper", side_effect=fakes.TimeStamper),
        patch(
            "structlog.processors.format_exc_info", side_effect=fakes.format_exc_info
        ),
    ):
        yield


@pytest.fixture
def logger(mock_logger_env: None) -> Generator[WrappedLogger, None, None]:
    """Setup a logger for testing and return it"""

    structlog.reset_defaults()

    processors = structlog_gcp.build_processors()
    structlog.configure(processors=processors)
    logger = structlog.get_logger()
    yield logger

    structlog.reset_defaults()


T_stdout = Callable[[], str]


@pytest.fixture
def stdout(capsys: CaptureFixture[str]) -> T_stdout:
    def read() -> str:
        output = capsys.readouterr()
        assert "" == output.err
        return output.out

    return read
