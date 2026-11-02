"""Flights page: search, budget flights, occupancy, flight details."""
import streamlit as st

from airport_system.db import crud, procedures, reports
from airport_system.views.common import (city_select, company_select, period,
                                         result_table, run)


_FLIGHT_COLUMNS = [
    ('flight_timestamp', 'Departure', 'datetime'),
    ('from_city', 'From', 'text'),
    ('to_city', 'To', 'text'),
    ('price', 'Price', 'money'),
    ('company_name', 'Manufacturer', 'text'),
    ('model_name', 'Model', 'text'),
]


def _search_tab() -> None:
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        from_city = city_select('From', 'search_from', c1)
        to_city = city_select('To', 'search_to', c2)
        company = company_select('Manufacturer', 'search_company', c3)
        date_from, date_to = period('search_period', 'Departure')

    rows = run(reports.search_flights, from_city, to_city, date_from, date_to, company)
    if rows is not None:
        st.caption(f'{len(rows)} flight(s) found')
    result_table(rows, _FLIGHT_COLUMNS)


def _budget_tab() -> None:
    st.caption('Flights priced below the average price of all flights.')
    with st.container(border=True):
        c1, c2 = st.columns(2)
        from_city = city_select('From', 'budget_from', c1)
        to_city = city_select('To', 'budget_to', c2)
        date_from, date_to = period('budget_period', 'Departure')

    rows = run(reports.budget_flights, from_city, to_city, date_from, date_to)
    result_table(rows, _FLIGHT_COLUMNS)


def _occupancy_tab() -> None:
    with st.container(border=True):
        date_from, date_to = period('occupancy_period', 'Departure')

    rows = run(reports.occupancy_per_flight, date_from, date_to)
    if rows:
        for row in rows:
            row['occupancy'] = row['seats_occupied'] / row['seats_capacity']
        taken = sum(r['seats_occupied'] for r in rows)
        capacity = sum(r['seats_capacity'] for r in rows)
        m1, m2, m3 = st.columns(3)
        m1.metric('Flights', len(rows))
        m2.metric('Seats taken', f'{taken} / {capacity}')
        m3.metric('Average occupancy', f'{taken / capacity:.1%}')

    result_table(rows, [
        ('flight_timestamp', 'Departure', 'datetime'),
        ('from_city', 'From', 'text'),
        ('to_city', 'To', 'text'),
        ('company_name', 'Manufacturer', 'text'),
        ('model_name', 'Model', 'text'),
        ('seats_occupied', 'Taken', 'int'),
        ('seats_capacity', 'Capacity', 'int'),
        ('occupancy', 'Occupancy', 'text'),
    ], extra_config={
        'Occupancy': st.column_config.ProgressColumn(
            'Occupancy', format='percent', min_value=0, max_value=1),
    })


def flight_details(flight_id: int) -> None:
    """Statistics (sp_flight_stats) and passenger list of one flight.

    Also used by the ℹ️ popup in the Flights table on the Manage data page.
    """
    stats = run(procedures.flight_stats, flight_id)
    if stats is None:
        return
    m1, m2, m3 = st.columns(3)
    m1.metric('Tickets sold', stats['tickets_sold'])
    m2.metric('Revenue', f'{stats["revenue"]:,.2f}')
    m3.metric('Free seats', stats['free_seats'])

    st.markdown('**Passengers**')
    result_table(run(reports.passengers_per_flight, flight_id), [
        ('passport_id', 'Passport', 'text'),
        ('passenger_name', 'Name', 'text'),
        ('seat', 'Seat', 'text'),
        ('seat_class', 'Class', 'text'),
    ])


def _details_tab() -> None:
    flights = crud.list_options('flight')
    if not flights:
        st.info('There are no flights yet.')
        return
    labels = dict(flights)
    with st.container(border=True):
        flight_id = st.selectbox('Flight', list(labels), format_func=labels.get,
                                 key='details_flight')
    flight_details(flight_id)


def render() -> None:
    st.title('Flights')
    search, budget, occupancy, details = st.tabs(
        ['Search', 'Budget flights', 'Occupancy', 'Flight details'])
    with search:
        _search_tab()
    with budget:
        _budget_tab()
    with occupancy:
        _occupancy_tab()
    with details:
        _details_tab()
