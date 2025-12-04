import os
from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error


def load_db_config():
    """
    Load DB configuration from config.py if present; fall back to config_example.py.
    Environment variables can override keys for portability.
    """
    try:
        import config as cfg  # type: ignore
    except ImportError:
        import config_example as cfg  # type: ignore

    return {
        "host": os.getenv("DB_HOST", getattr(cfg, "MYSQL_HOST", "localhost")),
        "user": os.getenv("DB_USER", getattr(cfg, "MYSQL_USER", "root")),
        "password": os.getenv("DB_PASSWORD", getattr(cfg, "MYSQL_PASSWORD", "")),
        "database": os.getenv("DB_NAME", getattr(cfg, "MYSQL_DB", "")),
        "port": int(os.getenv("DB_PORT", getattr(cfg, "MYSQL_PORT", 3306))),
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
