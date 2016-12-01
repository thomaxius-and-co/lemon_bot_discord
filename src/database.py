import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

@contextmanager
def connect():
    connect_string = "host=localhost dbname=%s user=%s password=%s" % (
        os.environ["DATABASE_NAME"],
        os.environ["DATABASE_USERNAME"],
        os.environ["DATABASE_PASSWORD"]
    )
    with psycopg2.connect(connect_string, cursor_factory=RealDictCursor) as con:
        with con.cursor() as c:
            yield c

def initialize_schema():
    with connect() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS start_times (
                ts timestamp NOT NULL,
                message TEXT
            );
        """)

def insert_start_time(message):
    with connect() as c:
        c.execute("""
            INSERT INTO start_times (ts, message)
            VALUES (current_timestamp, %s)
        """, [message])

