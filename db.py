import os
from contextlib import contextmanager

from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# Load .env if present
load_dotenv()


def load_db_config():
    """
    Load DB configuration from environment variables.
    Expected keys: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT.
    """
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", ""),
        "port": int(os.getenv("DB_PORT", 3306)),
    }


@contextmanager
def get_connection():
    conn = None
    try:
        conn = mysql.connector.connect(**load_db_config())
        yield conn
    finally:
        if conn:
            conn.close()


def run_query(query, params=None, fetch=None, return_lastrowid=False):
    params = params or ()
    with get_connection() as conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(query, params)
            result = None
            if fetch == "one":
                result = cur.fetchone()
            elif fetch == "all":
                result = cur.fetchall()
            lastrowid = cur.lastrowid
            conn.commit()
            return lastrowid if return_lastrowid else result
        except Error as exc:
            conn.rollback()
            raise exc


def fetch_all(query, params=None):
    return run_query(query, params=params, fetch="all")


def fetch_one(query, params=None):
    return run_query(query, params=params, fetch="one")
