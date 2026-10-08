import os
from dotenv import load_dotenv
import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from airport_system.db.queries import REVENUE_BY_CLASS_QUERY, FREQUENT_TRAVELERS_QUERY, BUDGET_FLIGHTS_QUERY, \
    NO_FLIGHT_PLANES_QUERY

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


def query(sql, params=None) -> list[dict]:
    with get_connection() as connection:
        return connection.execute(sql, params).fetchall()

# Test
print(query(NO_FLIGHT_PLANES_QUERY, {'date_from': None, "date_to": None, "company": None}))