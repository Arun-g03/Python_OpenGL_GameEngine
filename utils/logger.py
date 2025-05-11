import threading
from utils.settings import LOG_DEBUG

class Logger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def log(self, *args, **kwargs):
        if LOG_DEBUG:
            print('[DEBUG]', *args, **kwargs)

logger = Logger() 