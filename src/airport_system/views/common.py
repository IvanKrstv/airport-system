"""Shared building blocks for the report pages: filters, error handling, result tables."""
from datetime import date
from decimal import Decimal

import psycopg
import streamlit as st

from airport_system.db.connection import query


# ---------------------------------------------------------------- errors

def error_text(error: psycopg.Error) -> str:
    """Readable message for a database error."""
    diag = error.diag
    primary = diag.message_primary or str(error)
    detail = diag.message_detail

    if isinstance(error, psycopg.errors.RaiseException):
        return primary                      # message from RAISE EXCEPTION in a procedure
    if isinstance(error, psycopg.errors.ForeignKeyViolation):
        text = 'The record is linked to other records and cannot be deleted (or it points to a non-existent record).'
    elif isinstance(error, psycopg.errors.UniqueViolation):
        text = 'A record with this value already exists.'
    elif isinstance(error, psycopg.errors.CheckViolation):
        return f'The value violates a constraint ({diag.constraint_name}).'
    else:
        text = primary
    return f'{text} {detail}' if detail else text


def run(fetch, *args, **kwargs):
    """Calls a report function; shows the error and returns None if it fails."""
    try:
        return fetch(*args, **kwargs)
    except ValueError as error:
        st.error(str(error))
    except psycopg.Error as error:
        st.error(error_text(error))
    return None


# ---------------------------------------------------------------- filters

def period(key: str, label: str = 'Period') -> tuple[date | None, date | None]:
    """Two optional date inputs side by side. Empty means 'no limit'."""
    left, right = st.columns(2)
    date_from = left.date_input(f'{label} from', value=None, key=f'{key}_from',
                                format='YYYY-MM-DD')
    date_to = right.date_input(f'{label} to', value=None, key=f'{key}_to',
                               format='YYYY-MM-DD')
    return date_from, date_to


def _names(sql: str) -> list[str]:
    return [row['name'] for row in query(sql)]


def city_select(label: str, key: str, container=st) -> str | None:
    # noinspection SqlResolve
    cities = _names('SELECT DISTINCT city_name AS name FROM Destination ORDER BY name')
    return container.selectbox(label, [None, *cities], key=key,
                               format_func=lambda c: 'All' if c is None else c)


def company_select(label: str, key: str, container=st) -> str | None:
    # noinspection SqlResolve
    companies = _names('SELECT company_name AS name FROM Company ORDER BY name')
    return container.selectbox(label, [None, *companies], key=key,
                               format_func=lambda c: 'All' if c is None else c)


# ---------------------------------------------------------------- results

# Column kinds -> how the column is formatted in st.dataframe
_FORMATS = {
    'text': lambda label: st.column_config.TextColumn(label),
    'int': lambda label: st.column_config.NumberColumn(label, format='%d'),
    'money': lambda label: st.column_config.NumberColumn(label, format='%.2f'),
    'datetime': lambda label: st.column_config.DatetimeColumn(label, format='YYYY-MM-DD HH:mm'),
}


def result_table(rows: list[dict] | None, columns: list[tuple[str, str, str]],
                 extra_config: dict | None = None) -> None:
    """Shows query rows as a sortable table.

    columns: (key in the row, header shown in the UI, kind) - kind is one of _FORMATS.
    Only the listed columns are shown, in that order.
    """
    if rows is None:                        # the query failed; the error is already shown
        return
    if not rows:
        st.info('No results for these filters.')
        return

    data = [{label: _plain(row.get(key)) for key, label, _ in columns} for row in rows]
    config = {label: _FORMATS[kind](label) for _, label, kind in columns}
    config.update(extra_config or {})
    st.dataframe(data, hide_index=True, column_config=config)


def _plain(value):
    """Decimal -> float so that charts and number formatting work."""
    return float(value) if isinstance(value, Decimal) else value


def total(rows: list[dict] | None, key: str) -> float:
    return sum(_plain(row[key]) or 0 for row in rows or [])


def bar_chart(rows: list[dict] | None, label_key: str, value_key: str, value_label: str) -> None:
    """Horizontal single-series bar chart (one colour, no legend; hover shows the value)."""
    if not rows:
        return
    data = [{'name': row[label_key], value_label: _plain(row[value_key])} for row in rows]
    st.bar_chart(data, x='name', y=value_label, x_label='', y_label=value_label,
                 horizontal=True, sort=f'-{value_label}',
                 height=max(160, 44 * len(data)))
