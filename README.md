# Google Cloud Logging formatter for `structlog`

This is an opiniated package that configures [structlog](https://structlog.org/)
to output log compatible with the [Google Cloud Logging log
format](https://cloud.google.com/logging/docs/structured-logging).

The intention of this package is to be used for applications that run in [Google
Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine/) or [Google
Cloud Function](https://cloud.google.com/functions/), or any other systems that
know how to send logs to Google Cloud.

As such, the package is only concerned about **formatting logs**, where logs are
expected to be written on the standard output. Sending the logs to the actual
Google Logging API is supposed to be done by an external agent.


In particular, this package provides the following configuration by default:

* Logs are formatted as JSON using the [Google Cloud Logging log
  format](https://cloud.google.com/logging/docs/structured-logging)
* The [Python standard library's
  `logging`](https://docs.python.org/3/library/logging.html) log levels are
  available and translated to their GCP equivalents.
* Exceptions and `CRITICAL` log messages will be reported into [Google Error
  Reporting dashboard](https://cloud.google.com/error-reporting/)
* Additional logger bound arguments will be reported as `labels` in GCP.


## How to use?

Install the package with `pip` or your favorite Python package manager:

```sh
pip install structlog-gcp
```

Then, configure `structlog` as usual, using the Structlog processors the package
provides:

```python
import structlog
import structlog_gcp

processors = structlog_gcp.build_processors()
structlog.configure(processors=processors)
```

Then, you can use `structlog` as usual:

```python
logger = structlog.get_logger().bind(arg1="something")

logger.info("Hello world")

converted = False
try:
    int("foobar")
    converted = True
except:
    logger.exception("Something bad happens")

if not converted:
    logger.critical("This is not supposed to happen", converted=converted)
```

## Examples

Check out the [`examples` folder](tree/main/examples) to see how it can be used.

* How it should appear in the Google Cloud Logging log explorer:
  ![](https://raw.githubusercontent.com/multani/structlog-gcp/main/docs/logs.pn)

* How it should appear in the Google Cloud Error Reporting dashboard:
  ![](https://raw.githubusercontent.com/multani/structlog-gcp/docs/errors.png)


## Reference

* https://cloud.google.com/logging/docs/structured-logging
* https://cloud.google.com/error-reporting/docs/formatting-error-messages
* https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry
