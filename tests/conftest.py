from unittest.mock import patch

import pytest
import structlog

import structlog_gcp

from . import fakes


@pytest.fixture
def mock_logger_env():
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
def logger(mock_logger_env):
    """Setup a logger for testing and return it"""

    structlog.reset_defaults()

    processors = structlog_gcp.build_processors()
    structlog.configure(processors=processors)
    logger = structlog.get_logger()
    yield logger

    structlog.reset_defaults()


@pytest.fixture
def stdout(capsys):
    def read():
        output = capsys.readouterr()
        assert "" == output.err
        return output.out

    yield read
