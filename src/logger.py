import logging
import json
import os
from logging import Formatter, LogRecord
from datetime import datetime

def init():
    if json_log_enabled():
        logHandler = logging.StreamHandler()
        logHandler.setFormatter(JsonFormatter())
        logging.basicConfig(level=logging.INFO, handlers=[logHandler])
    else:
        FORMAT = '%(asctime)s %(levelname)s %(name)s %(message)s'
        logging.basicConfig(level=logging.INFO, format=FORMAT)

    # Make discord.py log a bit less
    for name in ['discord', 'websockets']:
        logging.getLogger(name).setLevel(logging.INFO)

    for name in ['CACHE']:
        logging.getLogger(name).setLevel(logging.INFO)

def json_log_enabled():
    return os.environ.get("LOG_JSON", "false") == "true"


def get(name):
    return logging.getLogger(name)

class JsonFormatter(Formatter):
    def __init__(self):
        super().__init__()

    def format(self, record: LogRecord) -> str:
        return json.dumps({
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        })