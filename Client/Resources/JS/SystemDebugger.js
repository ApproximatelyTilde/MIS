const SystemDebugger = {
  LogMessage: function (Level, Message) {
    const EnvironmentMeta = document.querySelector("meta[name=\"Environment\"]");
    if (!EnvironmentMeta) {
      return;
    }
    const Environment = EnvironmentMeta.getAttribute("content");
    if (Environment !== "development" && Level === "DEBUG") {
      return;
    }
    const CurrentDate  = new Date();
    const YearString   = String(CurrentDate.getFullYear());
    const MonthString  = String(CurrentDate.getMonth() + 1).padStart(2, "0");
    const DayString    = String(CurrentDate.getDate()).padStart(2, "0");
    const HourString   = String(CurrentDate.getHours()).padStart(2, "0");
    const MinuteString = String(CurrentDate.getMinutes()).padStart(2, "0");
    const CurrentTime  = YearString + MonthString + DayString + " - " + HourString + MinuteString;
    let FunctionName = "";
    const ErrorStack = new Error().stack;
    if (ErrorStack) {
      const StackLines = ErrorStack.split("\n");
      for (let Index = 1; Index < StackLines.length; Index += 1) {
        const LineText = StackLines[Index].trim();
        if (LineText.indexOf("SystemDebugger.") !== -1 || LineText.indexOf("LogMessage") !== -1) {
          continue;
        }
        const ChromiumMatch = LineText.match(/at\s+(?:new\s+)?(?:async\s+)?([^\s(]+)\s+\(/);
        if (ChromiumMatch && ChromiumMatch[1]) {
          let ExtractedName = ChromiumMatch[1];
          if (ExtractedName.indexOf("Object.") === 0) {
            ExtractedName = ExtractedName.substring(7);
          }
          if (ExtractedName !== "<anonymous>" && ExtractedName !== "anonymous" && ExtractedName !== "Anonymous") {
            FunctionName = ExtractedName;
            break;
          }
        }
        const FirefoxMatch = LineText.match(/^(?:async\*|.*?\*)?([^@\s(]+)@/);
        if (FirefoxMatch && FirefoxMatch[1]) {
          let ExtractedName = FirefoxMatch[1];
          if (ExtractedName.indexOf("/") !== -1) {
            ExtractedName = ExtractedName.split("/")[0];
          }
          if (ExtractedName !== "<anonymous>" && ExtractedName !== "anonymous" && ExtractedName !== "Anonymous") {
            FunctionName = ExtractedName;
            break;
          }
        }
      }
      if (!FunctionName) {
        for (let Index = 1; Index < StackLines.length; Index += 1) {
          const LineText = StackLines[Index].trim();
          if (LineText.indexOf("SystemDebugger.") !== -1 || LineText.indexOf("LogMessage") !== -1) {
            continue;
          }
          const LocationMatch = LineText.match(/([a-zA-Z0-9_\-]+\.js):(\d+)(?::\d+)?/);
          if (LocationMatch) {
            FunctionName = LocationMatch[1] + ":" + LocationMatch[2];
            break;
          }
        }
      }
    }
    if (!FunctionName || FunctionName === "<anonymous>" || FunctionName === "anonymous" || FunctionName === "Anonymous") {
      FunctionName = "SystemScope";
    }
    const NormalizedLevel   = (Level === "WARN" || Level === "WARNING") ? "WARNING" : Level;
    const ColonPadding      = ":".padEnd(10 - NormalizedLevel.length, " ");
    let LevelStyle = "color: var(--Color2); font-weight: bold;";
    if (NormalizedLevel === "DEBUG") {
      LevelStyle = "color: var(--Color6); font-weight: bold;";
    } else if (NormalizedLevel === "WARNING") {
      LevelStyle = "color: var(--Color3); font-weight: bold;";
    } else if (NormalizedLevel === "ERROR") {
      LevelStyle = "color: var(--Color1); font-weight: bold;";
    } else if (NormalizedLevel === "CRITICAL") {
      LevelStyle = "color: var(--Color15); background-color: var(--Color1); font-weight: bold; padding: 1px 4px;";
    }
    const ResetStyle        = "color: inherit; font-weight: normal;";
    const FunctionNameStyle = "color: inherit; font-weight: bold;";
    const OutputFormat      = "%c" + NormalizedLevel + "%c" + ColonPadding + CurrentTime + " - %c@" + FunctionName + "%c: " + Message;
    if (Level === "ERROR" || Level === "CRITICAL") {
      console.error(OutputFormat, LevelStyle, ResetStyle, FunctionNameStyle, ResetStyle);
    } else if (Level === "WARNING" || Level === "WARN") {
      console.warn(OutputFormat, LevelStyle, ResetStyle, FunctionNameStyle, ResetStyle);
    } else if (Level === "INFO") {
      console.info(OutputFormat, LevelStyle, ResetStyle, FunctionNameStyle, ResetStyle);
    } else {
      console.debug(OutputFormat, LevelStyle, ResetStyle, FunctionNameStyle, ResetStyle);
    }
  }
};

window.SystemDebugger = SystemDebugger;
