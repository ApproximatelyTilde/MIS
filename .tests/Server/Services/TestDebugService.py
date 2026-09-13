import logging                      as Logging
import Server.Config                as Config
import Server.Services.DebugService as DebugService

class TestDebugService:
    def TestLogLevelEnumValues(self) -> None:
        assert (DebugService.LogLevel.Debug.value == Logging.DEBUG)
        assert (DebugService.LogLevel.Info.value == Logging.INFO)
        assert (DebugService.LogLevel.Warning.value == Logging.WARNING)
        assert (DebugService.LogLevel.Error.value == Logging.ERROR)
        assert (DebugService.LogLevel.Critical.value == Logging.CRITICAL)

    def TestEnvironmentLogFilter(self) -> None:
        LogFilterInstance  : DebugService.EnvironmentLogFilter = DebugService.EnvironmentLogFilter()
        DebugRecord        : Logging.LogRecord                 = Logging.LogRecord("Zibell", Logging.DEBUG, "path", 1, "Debug log", (), None)
        InfoRecord         : Logging.LogRecord                 = Logging.LogRecord("Zibell", Logging.INFO, "path", 1, "Info log", (), None)

        OriginalEnvironment: str                               = Config.GLOBAL_SETTINGS.ENVIRONMENT
        try:
            Config.GLOBAL_SETTINGS.ENVIRONMENT                 = "development"
            assert (LogFilterInstance.filter(DebugRecord) is True)
            assert (LogFilterInstance.filter(InfoRecord) is True)

            Config.GLOBAL_SETTINGS.ENVIRONMENT                 = "production"
            assert (LogFilterInstance.filter(DebugRecord) is False)
            assert (LogFilterInstance.filter(InfoRecord) is True)

        finally:
            Config.GLOBAL_SETTINGS.ENVIRONMENT                 = OriginalEnvironment

    def TestAccessLogFilterSilencedRoutes(self) -> None:
        AccessFilterInstance: DebugService.AccessLogFilter = DebugService.AccessLogFilter()
        SilencedRecord      : Logging.LogRecord            = Logging.LogRecord("uvicorn.access", Logging.INFO, "path", 1, "GET /API/Mail/Status HTTP/1.1 200", (), None)
        AllowedRecord       : Logging.LogRecord            = Logging.LogRecord("uvicorn.access", Logging.INFO, "path", 1, "GET /API/Characters HTTP/1.1 200", (), None)

        assert (AccessFilterInstance.filter(SilencedRecord) is False)
        assert (AccessFilterInstance.filter(AllowedRecord) is True)

    def TestDebugLogFormatter(self) -> None:
        FormatterInstance: DebugService.DebugLogFormatter = DebugService.DebugLogFormatter()
        RecordInstance   : Logging.LogRecord              = Logging.LogRecord("Zibell", Logging.INFO, "path", 1, "Standard log message", (), None)
        RecordInstance.created                            = 1700000000.0
        RecordInstance.DisplayTag                         = "TestTag"

        FormattedOutput  : str                            = FormatterInstance.format(RecordInstance)
        assert ("INFO" in FormattedOutput)
        assert ("@TestTag" in FormattedOutput)
        assert ("Standard log message" in FormattedOutput)
