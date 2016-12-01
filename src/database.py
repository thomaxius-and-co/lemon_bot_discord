import psycopg2

def db_connect():
    return psycopg2.connect("host=localhost dbname=%s user=%s password=%s" % (
        os.environ["DATABASE_NAME"],
        os.environ["DATABASE_USERNAME"],
        os.environ["DATABASE_PASSWORD"]
    ))

def

def initialize_schema():
    with db_connect() as conn:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS start_times (
                    ts timestamp NOT NULL,
                    message TEXT
                );
            """)

def insert_start_time(message):
    with db_connect() as conn:
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO start_times (ts, message)
                VALUES (current_timestamp, %s)
            """, [message])

