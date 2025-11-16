import streamlit as st
from utils.mongo_client import get_db_stats

def display_platform_dashboard():
    st.header("🚀 Platform Status")
    
    stats = get_db_stats()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Events Processed", f"{stats.get('enriched_events', 0):,}")
    col2.metric("Chat Messages", f"{stats.get('chat_messages', 0):,}")
    col3.metric("Market Trades", f"{stats.get('market_trades', 0):,}")
    
    total_anomalies = stats.get('chat_anomalies', 0) + stats.get('market_anomalies', 0)
    col4.metric("Total Anomalies Detected", f"{total_anomalies:,}")
    
    st.info("This dashboard provides a high-level overview of the data flowing through the system. Metrics are based on document counts in MongoDB collections and update every few seconds.")

    st.subheader("Next Steps")
    st.markdown("""
    - **Kafka UI**: [http://localhost:8080](http://localhost:8080) to inspect Kafka topics and consumer groups.
    - **Mongo Express**: [http://localhost:8081](http://localhost:8081) to browse the MongoDB collections directly.
    - **Spark UI**: [http://localhost:8082](http://localhost:8082) to monitor the Spark jobs and cluster status.
    """)