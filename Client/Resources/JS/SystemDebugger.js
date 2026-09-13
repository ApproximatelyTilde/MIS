const SystemDebugger = {
  LogDebugMessage: function (Message) {
    const EnvironmentMeta = document.querySelector('meta[name="Environment"]');
    if (!EnvironmentMeta) {
      return;
    }
    const Environment = EnvironmentMeta.getAttribute("content");
    if (Environment !== "development") {
      return;
    }
    const CurrentTime = new Date().toISOString();
    let FunctionName = "Anonymous";
    const ErrorStack = new Error().stack;
    if (ErrorStack) {
      const StackLines = ErrorStack.split("\n");
      let CallerLine = "";
      if (StackLines.length > 0 && StackLines[0].indexOf("LogDebugMessage") !== -1) {
        if (StackLines.length > 1) {
          CallerLine = StackLines[1].trim();
        }
      } else if (StackLines.length > 1 && StackLines[1].indexOf("LogDebugMessage") !== -1) {
        if (StackLines.length > 2) {
          CallerLine = StackLines[2].trim();
        }
      } else if (StackLines.length > 2) {
        CallerLine = StackLines[2].trim();
      }
      if (CallerLine.length > 0) {
        const ChromiumMatch = CallerLine.match(/at\s+(?:new\s+)?(?:async\s+)?([^\s(]+)\s+\(/);
        if (ChromiumMatch) {
          FunctionName = ChromiumMatch[1];
          if (FunctionName.indexOf("Object.") === 0) {
            FunctionName = FunctionName.substring(7);
          }
        } else {
          const FirefoxMatch = CallerLine.match(/^(?:async\*|.*?\*)?([^@\s(]+)@/);
          if (FirefoxMatch && FirefoxMatch[1]) {
            FunctionName = FirefoxMatch[1];
            if (FunctionName.indexOf("/") !== -1) {
              FunctionName = FunctionName.split("/")[0];
            }
          }
        }
      }
    }
    const DebugOutput = "[DEBUG  ] [" + CurrentTime + "] [" + FunctionName + "] " + Message;
    console.debug(DebugOutput);
  }
};

window.SystemDebugger = SystemDebugger;
