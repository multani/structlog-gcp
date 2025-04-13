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

* Logs are formatted as JSON using the [Google Cloud Logging log format](https://cloud.google.com/logging/docs/structured-logging)
* The [Python standard library's `logging`](https://docs.python.org/3/library/logging.html)
  log levels are available and translated to their GCP equivalents.
* Exceptions and `CRITICAL` log messages will be reported into [Google Error Reporting dashboard](https://cloud.google.com/error-reporting/)
* Additional logger bound arguments will be reported into the `jsonPayload` event.


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

try:
    1 / 0
except ZeroDivisionError as exc:
    logger.info("This was known to happen! {exc}")
```

The `structlog_gcp.build_processors()` function constructs structlog processors to:

* Output logs as Google Cloud Logging format using the default Python JSON serializer.
* Carry context variables across loggers (see [structlog: Context Variables](https://www.structlog.org/en/stable/contextvars.html))

For more advanced usage, see [Advanced Configuration](#advanced-configuration)


### Errors


Errors are automatically reported to the [Google Error Reporting service](https://cloud.google.com/error-reporting/), most of the time.

#### Using `logger.exception`

Using:

```python
try:
    1 / 0
except:
    logger.exception("oh no")
```

Will give you:

* The current exception can automatically added into the log event
* The log level will be `ERROR`
* The exception will be reported in Error Reporting

##### Using `logger.$LEVEL(..., exception=exc)`

Using:

```python
try:
    1 / 0
except Exception as exc
    logger.info("oh no", exception=exc)
```
Will give you:

* The specified exception will be part of the log event
* The log level will be `INFO`, or whichever log level you used
* The exception will be reported in Error Reporting


##### Using `logger.$LEVEL(...)`

Not passing any `exception` argument to the logger, as in:

```python
try:
    1 / 0
except Exception as exc
    logger.warning(f"oh no: {exc}")
```

Will give you:

* The exception will **not** be part of the log event.
* The log level will be `WARNING` (or whichever log level you used)
* AND the exception will **not** be reported in Error Reporting

### Configuration

You can configure the service name and the version used during the report with 2 different ways:

* By default, the library assumes to run with Cloud Run environment
  variables configured, in particular [the `K_SERVICE` and `K_REVISION` variables](https://cloud.google.com/run/docs/configuring/services/overview-environment-variables#reserved_environment_variables_for_functions).
* You can also pass the service name and revision at configuration time with:

  ```python
  import structlog
  import structlog_gcp

  processors = structlog_gcp.build_processors(
      service="my-service",
      version="v1.2.3",
  )
  structlog.configure(processors=processors)
  ```

### Advanced Configuration

If you need to have more control over the processors configured by the library, you can use the `structlog_gcp.build_gcp_processors()` builder function.

This function only configures the Google Cloud Logging-specific processors and omits all the rest.

In particular, you can use this function:

* If you want to have more control over the processors to be configured in structlog. You can prepend or append other processors around the Google-specific ones.
* If you want to serialize using another JSON serializer or with specific options.

For instance:


```python
import orjson
import structlog
from structlog.processors import JSONRenderer

import structlog_gcp


def add_open_telemetry_spans(...):
    # Cf. https://www.structlog.org/en/stable/frameworks.html#opentelemetry
    ...

gcp_processors = structlog_gcp.build_gcp_processors()

# Fine-tune processors
processors = [add_open_telemetry_spans]
processors.extend(gcp_processors)
processors.append(JSONRenderer(serializer=orjson.dumps))

structlog.configure(processors=processors)
```

> [!IMPORTANT]
>
> `structlog_gcp.build_gcp_processors()` **doesn't** configure a renderer and
> you must supply a JSON renderer of your choice for the library to work
> correctly.


## Examples

Check out the [`examples` folder](https://github.com/multani/structlog-gcp/tree/main/examples) to see how it can be used.

* How it should appear in the Google Cloud Logging log explorer:
  ![](https://raw.githubusercontent.com/multani/structlog-gcp/main/docs/logs.png)

* How it should appear in the Google Cloud Error Reporting dashboard:
  ![](https://raw.githubusercontent.com/multani/structlog-gcp/main/docs/errors.png)


## Reference

* https://cloud.google.com/logging/docs/structured-logging
* https://cloud.google.com/error-reporting/docs/formatting-error-messages
* https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry
