import psycopg2
from psycopg2 import sql
from contextlib import contextmanager
import os

@contextmanager
def get_external_db():
    conn = psycopg2.connect(
        host=os.getenv("EXTERNAL_DB_HOST"),
        dbname=os.getenv("EXTERNAL_DB_NAME"),
        user=os.getenv("EXTERNAL_DB_USER"),
        password=os.getenv("EXTERNAL_DB_PASSWORD"),
        port=os.getenv("EXTERNAL_DB_PORT", "5432")
    )
    try:
        yield conn
    finally:
        conn.close()