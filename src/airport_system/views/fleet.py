"""Fleet & passengers page: planes without flights, frequent travelers."""
import streamlit as st

from airport_system.db import reports
from airport_system.views.common import company_select, period, result_table, run


def _idle_planes_tab() -> None:
    st.caption('Planes that have no flight in the selected period.')
    with st.container(border=True):
        company = company_select('Manufacturer', 'idle_company')
        date_from, date_to = period('idle_period', 'Flights')

    rows = run(reports.no_flight_planes, date_from, date_to, company)
    if rows is not None:
        st.caption(f'{len(rows)} plane(s)')
    result_table(rows, [
        ('license_plate', 'Registration', 'text'),
        ('company_name', 'Manufacturer', 'text'),
        ('model_name', 'Model', 'text'),
        ('model_capacity', 'Capacity', 'int'),
    ])


def _frequent_travelers_tab() -> None:
    st.caption('Passengers with at least the given number of flights in the last N months '
               '(by departure date, up to today).')
    with st.container(border=True):
        left, right = st.columns(2)
        months = left.number_input('Last N months', min_value=1, value=6, step=1,
                                   key='frequent_months')
        min_trips = right.number_input('Minimum trips', min_value=1, value=2, step=1,
                                       key='frequent_min_trips')

    rows = run(reports.frequent_travelers, int(months), int(min_trips))
    result_table(rows, [
        ('passenger_name', 'Passenger', 'text'),
        ('nationality', 'Nationality', 'text'),
        ('total_trips', 'Trips', 'int'),
    ])


def render() -> None:
    st.title('Fleet & passengers')
    idle, frequent = st.tabs(['Planes without flights', 'Frequent travelers'])
    with idle:
        _idle_planes_tab()
    with frequent:
        _frequent_travelers_tab()
