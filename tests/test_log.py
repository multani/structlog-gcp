import json


def test_normal(capsys, logger):
    logger.info("test")

    output = capsys.readouterr()

    assert "" == output.err

    msg = json.loads(output.out)

    expected = {
        "logging.googleapis.com/sourceLocation": {
            "file": "/app/test.py",
            "function": "test:test123",
            "line": "42",
        },
        "message": "test",
        "severity": "INFO",
        "time": "2023-04-01T08:00:00.000000Z",
    }
    assert expected == msg


def test_error(capsys, logger):
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("oh noes", foo="bar")

    output = capsys.readouterr()

    assert "" == output.err

    msg = json.loads(output.out)

    expected = {
        "@type": "type.googleapis.com/google.devtools.clouderrorreporting.v1beta1.ReportedErrorEvent",
        "context": {
            "reportLocation": {
                "file": "/app/test.py",
                "function": "test:test123",
                "line": "42",
            },
        },
        "logging.googleapis.com/sourceLocation": {
            "file": "/app/test.py",
            "function": "test:test123",
            "line": "42",
        },
        "serviceContext": {
            "service": "unknown service",
            "version": "unknown version",
        },
        "logging.googleapis.com/labels": {"foo": "bar"},
        "severity": "CRITICAL",
        "message": "oh noes",
        "stack_trace": "oh noes\nTraceback blabla",
        "time": "2023-04-01T08:00:00.000000Z",
    }
    assert expected == msg
