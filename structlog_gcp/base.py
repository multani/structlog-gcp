from . import errors, processors


class StructlogGCP:
    def __init__(self):
        pass

    def build_processors(self):
        procs = []

        procs.extend(processors.CoreCloudLogging().setup())
        procs.extend(processors.LogSeverity().setup())
        procs.extend(processors.CodeLocation().setup())
        procs.extend(errors.ReportException().setup())
        procs.extend(errors.ReportError(["CRITICAL"]).setup())
        procs.append(errors.add_service_context)
        procs.extend(processors.FormatAsCloudLogging().setup())

        return procs
