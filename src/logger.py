import logging

def init():
    # Configure logging (https://docs.python.org/3/library/logging.html#logrecord-attributes)
    FORMAT = '%(asctime)s %(levelname)s %(name)s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)

    # Make discord.py log a bit less
    for name in ['discord', 'websockets']:
        logging.getLogger(name).setLevel(logging.INFO)

    for name in ['CACHE']:
        logging.getLogger(name).setLevel(logging.INFO)

def get(name):
    return logging.getLogger(name)
