import streamlit as st
import time
from dotenv import load_dotenv

from components.chat_dashboard import display_chat_dashboard
from components.market_dashboard import display_market_dashboard
from components.platform_dashboard import display_platform_dashboard
from utils.mongo_client import MongoSingleton
from utils.style import local_css

load_dotenv()

# --- Page Config ---
st.set_page_config(
    page_title="DataFlow Stream Dashboard",
    page_icon="assets/favicon.ico",
    layout="wide"
)

# --- Load CSS ---
local_css("utils/style.css")

# --- Main App ---
def main():
    st.title("🌊 DataFlow Stream: Real-Time Analytics")

    # Initialize MongoDB connection
    try:
        mongo_client = MongoSingleton.get_instance()
        # Ping the server to check the connection
        mongo_client.admin.command('ping')
        st.sidebar.success("MongoDB Connected")
    except Exception as e:
        st.sidebar.error(f"MongoDB Connection Failed: {e}")
        st.error("Could not connect to the database. Please check the backend services.")
        return

    # --- Sidebar for Navigation ---
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Platform Status", "Twitch Chat Analytics", "Market Analytics"])

    # --- Page Routing ---
    if page == "Platform Status":
        display_platform_dashboard()
    elif page == "Twitch Chat Analytics":
        display_chat_dashboard()
    elif page == "Market Analytics":
        display_market_dashboard()
        import streamlit as st
import time
from dotenv import load_dotenv

from components.chat_dashboard import display_chat_dashboard
from components.market_dashboard import display_market_dashboard
from components.platform_dashboard import display_platform_dashboard
from utils.mongo_client import MongoSingleton
from utils.style import local_css

load_dotenv()

# --- Page Config ---
st.set_page_config(
    page_title="DataFlow Stream Dashboard",
    page_icon="assets/favicon.ico",
    layout="wide"
)

# --- Load CSS ---
local_css("utils/style.css")

# --- Main App ---
def main():
    st.title("🌊 DataFlow Stream: Real-Time Analytics")

    # Initialize MongoDB connection
    try:
        mongo_client = MongoSingleton.get_instance()
        # Ping the server to check the connection
        mongo_client.admin.command('ping')
        st.sidebar.success("MongoDB Connected")
    except Exception as e:
        st.sidebar.error(f"MongoDB Connection Failed: {e}")
        st.error("Could not connect to the database. Please check the backend services.")
        return

    # --- Sidebar for Navigation ---
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Platform Status", "Twitch Chat Analytics", "Market Analytics"])

    # --- Page Routing ---
    if page == "Platform Status":
        display_platform_dashboard()
    elif page == "Twitch Chat Analytics":
        display_chat_dashboard()
    elif page == "Market Analytics":
        display_market_dashboard()
        
    # --- Auto-refresh mechanism ---
    time.sleep(2) # Refresh interval in seconds
    st.rerun()

if __name__ == "__main__":
    main()
    # --- Auto-refresh mechanism ---
    time.sleep(2) # Refresh interval in seconds
    st.rerun()

if __name__ == "__main__":
    main()