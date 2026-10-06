import streamlit as st
from src.ui import inject_custom_css, render_sqlite_db_viewer

st.set_page_config(
    page_title="DocuMind AI - Database Explorer",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inject custom styling
inject_custom_css()

# Render SQLite DB Viewer
render_sqlite_db_viewer()
