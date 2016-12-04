import os
from contextlib import contextmanager

import psycopg2

@contextmanager
def connect():
    connect_string = "host=localhost dbname=%s user=%s password=%s" % (
        os.environ["DATABASE_NAME"],
        os.environ["DATABASE_USERNAME"],
        os.environ["DATABASE_PASSWORD"]
    )
    with psycopg2.connect(connect_string) as con:
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

        c.execute("""
            CREATE TABLE IF NOT EXISTS casino_account (
                discriminator TEXT NOT NULL,
                balance NUMERIC NOT NULL,
                PRIMARY KEY (discriminator)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS casino_bet (
                discriminator TEXT NOT NULL,
                bet NUMERIC NOT NULL,
                PRIMARY KEY (discriminator)
            );
        """)

def insert_start_time(message):
    with connect() as c:
        c.execute("""
            INSERT INTO start_times (ts, message)
            VALUES (current_timestamp, %s)
        """, [message])

