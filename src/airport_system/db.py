import os
from dotenv import load_dotenv
import psycopg
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg.sql import SQL

load_dotenv()

def get_connection(autocommit=False) -> Connection:
    return psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        row_factory=dict_row,
        autocommit=autocommit
    )


def query(sql: SQL, params=None) -> list[dict]:
    with get_connection() as connection:
        return connection.execute(sql, params).fetchall()

