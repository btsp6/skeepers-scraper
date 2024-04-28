import sys

class Logger:
    curr_message = ""
    message_count = 1

    @staticmethod
    def log(message: str) -> None:
        if message != Logger.curr_message:
            Logger.curr_message = message
            Logger.message_count = 1
            print(message)
            return
        
        Logger.message_count += 1
        sys.stdout.write("\033[F") # Cursor up one line
        sys.stdout.write("\033[K") # Clear to the end of line
        print(f"{message} ({Logger.message_count})")

