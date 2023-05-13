import logging

import functions_framework
import google.cloud.error_reporting
import google.cloud.logging
import structlog

import structlog_gcp

processors = structlog_gcp.build_processors()
structlog.configure(processors=processors)


@functions_framework.http
def test_func1(request):
    """Test the logging framework.

    * `GET` the deployed URL to trigger the `structlog-gcp` behavior
    * `POST` the deployed URL to trigger the official Google logging + error
      reporting libraries behavior
    * `DELETE` the deployed URL to crash the function and force a cold-restart
    """

    if request.method == "GET":
        logger = structlog.get_logger("test")

        logger.debug("a debug message", foo="bar")
        logger.info("an info message", foo="bar")
        logger.warning("a warning message", arg="something else")

        logger.error("an error message")
        logger.critical("a critical message with reported error")

        try:
            1 / 0
        except ZeroDivisionError:
            logger.exception("division by zero")

        try:
            raise TypeError("crash")
        except TypeError:
            logger.exception("type error")

    elif request.method == "POST":
        error = google.cloud.error_reporting.Client()
        google.cloud.logging.Client().setup_logging()

        logging.debug("a debug message")
        logging.info("an info message")
        logging.warning("a warning message")

        logging.error("an error message")
        logging.critical("a critical message with reported error")

        error.report("a reported error")

        try:
            1 / 0
        except ZeroDivisionError:
            error.report_exception()

        try:
            raise TypeError("crash")
        except TypeError:
            logging.exception("type error")

    elif request.method == "DELETE":
        # crash the function to force a cold restart
        raise RuntimeError("restart")

    return "OK"
