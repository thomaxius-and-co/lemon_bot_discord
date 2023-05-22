import functools
import inspect
import logging
import json
import os
from uuid import uuid4
from logging import Formatter, LogRecord
from datetime import datetime
from contextvars import ContextVar
from contextlib import contextmanager


_request_id_var: ContextVar[str] = ContextVar("request_id")


def with_request_id(func):
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with new_request_id():
                return await func(*args, **kwargs)
        return wrapper
    else:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with new_request_id():
                return func(*args, **kwargs)
        return wrapper


@contextmanager
def new_request_id():
    request_id = str(uuid4())
    token = _request_id_var.set(request_id)
    try:
        yield request_id
    finally:
        _request_id_var.reset(token)

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
        record_to_log = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "name": record.name,
            "level": record.levelname,
        }

        if isinstance(record.msg, dict):
            record_to_log["message"] = record.msg
        else:
            record_to_log["message"] = record.getMessage()

        if (request_id := _request_id_var.get(None)) is not None:
            record_to_log["requestId"] = request_id

        return json.dumps(record_to_log)
