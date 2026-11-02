import streamlit as st

from airport_system import crud_page

st.set_page_config(page_title='Airport System', layout='wide')
st.title('Airport System')

# Засега има само CRUD страницата; справките се добавят по-късно (например с st.tabs или страничен избор)
crud_page.render()