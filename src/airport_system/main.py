import streamlit as st

from airport_system import crud_page
from airport_system.views import fleet, flights, revenue


def _manage_data() -> None:
    st.title('Manage data')
    crud_page.render()


st.set_page_config(page_title='Airport System', page_icon='✈️', layout='wide')

page = st.navigation({
    'Airport System': [
        st.Page(_manage_data, title='Manage data', icon=':material/table_view:',
                url_path='data', default=True),
    ],
    'Reports': [
        st.Page(flights.render, title='Flights', icon=':material/flight_takeoff:',
                url_path='flights'),
        st.Page(revenue.render, title='Revenue', icon=':material/payments:',
                url_path='revenue'),
        st.Page(fleet.render, title='Fleet & passengers', icon=':material/airlines:',
                url_path='fleet'),
    ],
})

page.run()
