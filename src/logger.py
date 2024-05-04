import sys
from datetime import datetime
from zoneinfo import ZoneInfo

LOG_FORMAT = "[{now}] {message}"


class Logger:
    curr_message = ""
    message_count = 1

    @staticmethod
    def log(message: str) -> None:
        now = datetime.now(tz=ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S")
        if message != Logger.curr_message:
            Logger.curr_message = message
            Logger.message_count = 1
            print(LOG_FORMAT.format(now=now, message=message))
            return
        
        Logger.message_count += 1
        sys.stdout.write("\033[F") # Cursor up one line
        sys.stdout.write("\033[K") # Clear to the end of line
        print(LOG_FORMAT.format(now=now, message=f"{message} ({Logger.message_count})"))
