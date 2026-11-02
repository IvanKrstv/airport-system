"""Revenue page: revenue by route & class (function or cursor), by seat class, top destinations."""
import streamlit as st

from airport_system.db import procedures, reports
from airport_system.views.common import bar_chart, period, result_table, run, total


def _check_period(date_from, date_to) -> None:
    if date_from and date_to and date_from > date_to:
        raise ValueError('The start date cannot be after the end date.')


def _revenue_by_route(date_from, date_to, use_cursor: bool) -> list[dict]:
    _check_period(date_from, date_to)
    if use_cursor:
        return procedures.revenue_report_cursor(date_from, date_to)
    return procedures.revenue_report(date_from, date_to)


def _summary(rows: list[dict] | None, tickets_key: str, revenue_key: str) -> None:
    if not rows:
        return
    m1, m2 = st.columns(2)
    m1.metric('Total revenue', f'{total(rows, revenue_key):,.2f}')
    m2.metric('Tickets sold', int(total(rows, tickets_key)))


def _by_route_tab() -> None:
    with st.container(border=True):
        date_from, date_to = period('route_period', 'Sold')
        use_cursor = st.toggle('Use the cursor procedure', key='route_use_cursor')
    source = ('sp_revenue_report_cursor (procedure returning a refcursor)' if use_cursor
              else 'sp_revenue_report (function returning a table)')
    st.caption(f'Source: `{source}`')

    rows = run(_revenue_by_route, date_from, date_to, use_cursor)
    _summary(rows, 'tickets_sold', 'total_revenue')
    result_table(rows, [
        ('from_city', 'From', 'text'),
        ('to_city', 'To', 'text'),
        ('seat_class', 'Class', 'text'),
        ('tickets_sold', 'Tickets', 'int'),
        ('total_revenue', 'Revenue', 'money'),
    ])


def _by_class_tab() -> None:
    with st.container(border=True):
        date_from, date_to = period('class_period', 'Sold')

    rows = run(reports.revenue_per_seat_class, date_from, date_to)
    _summary(rows, 'tickets_sold', 'revenue')
    chart, table = st.columns(2)
    with chart:
        bar_chart(rows, 'seat_class', 'revenue', 'Revenue')
    with table:
        result_table(rows, [
            ('seat_class', 'Class', 'text'),
            ('tickets_sold', 'Tickets', 'int'),
            ('revenue', 'Revenue', 'money'),
        ])


def _top_destinations_tab() -> None:
    with st.container(border=True):
        top_n = st.number_input('Number of destinations', min_value=1, value=5, step=1,
                                key='top_n')
        date_from, date_to = period('top_period', 'Sold')

    rows = run(reports.top_destinations, int(top_n), date_from, date_to)
    chart, table = st.columns(2)
    with chart:
        bar_chart(rows, 'city_name', 'total_revenue', 'Revenue')
    with table:
        result_table(rows, [
            ('city_name', 'Destination', 'text'),
            ('total_tickets', 'Tickets', 'int'),
            ('total_revenue', 'Revenue', 'money'),
        ])


def render() -> None:
    st.title('Revenue')
    by_route, by_class, top = st.tabs(['By route & class', 'By seat class', 'Top destinations'])
    with by_route:
        _by_route_tab()
    with by_class:
        _by_class_tab()
    with top:
        _top_destinations_tab()
