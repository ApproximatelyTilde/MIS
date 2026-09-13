import Server.Config as Config
import datetime as DateTime
import inspect as Inspect
import sys as System

def LogDebugMessage(Message: str) -> None:
    if Config.GLOBAL_SETTINGS.ENVIRONMENT != "development":
        return
    CurrentTime: str = DateTime.datetime.now().isoformat()
    CallerFrame = Inspect.currentframe()
    if CallerFrame is None:
        FunctionName: str = "Anonymous"
    else:
        PreviousFrame = CallerFrame.f_back
        if PreviousFrame is None:
            FunctionName = "Anonymous"
        else:
            FunctionName = PreviousFrame.f_code.co_name
            del PreviousFrame
        del CallerFrame
    DebugOutput: str = "[DEBUG  ] [" + CurrentTime + "] [" + FunctionName + "] " + Message
    System.stdout.write(DebugOutput + "\n")
    System.stdout.flush()
