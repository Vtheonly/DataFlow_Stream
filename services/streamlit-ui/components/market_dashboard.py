import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.mongo_client import get_market_data, get_market_anomalies

def display_market_dashboard():
    st.header("📈 Market Analytics")

    market_data = get_market_data(limit=200)
    anomalies = get_market_anomalies(limit=50)

    if not market_data:
        st.warning("No market data found in the database yet.")
        return

    df_market = pd.DataFrame(market_data)
    df_market['timestamp'] = pd.to_datetime(df_market['timestamp'], unit='s')
    df_market = df_market.sort_values('timestamp')

    # --- Live Price Chart with Anomalies ---
    fig = go.Figure()

    # Price Line
    fig.add_trace(go.Scatter(
        x=df_market['timestamp'],
        y=df_market['payload'].apply(lambda x: x.get('price')),
        mode='lines',
        name='Price (BTCUSDT)'
    ))

    # Anomaly Markers
    if anomalies:
        df_anomalies = pd.DataFrame(anomalies)
        df_anomalies['timestamp'] = pd.to_datetime(df_anomalies['timestamp'], unit='s')
        fig.add_trace(go.Scatter(
            x=df_anomalies['timestamp'],
            y=df_anomalies['payload'].apply(lambda x: x.get('price')),
            mode='markers',
            marker=dict(color='red', size=10, symbol='x'),
            name='Anomaly Detected'
        ))

    fig.update_layout(title="Real-Time Market Price Feed", xaxis_title="Time", yaxis_title="Price (USD)")
    st.plotly_chart(fig, use_container_width=True)

    # --- Anomaly Feed ---
    st.subheader("Recent Market Anomalies")
    if anomalies:
        for anomaly in anomalies:
            anomaly_type = anomaly['enrichments']['anomaly'].get('type', 'N/A')
            price = anomaly['payload']['price']
            st.error(f"**{anomaly_type.replace('_', ' ').title()}** detected at price **${price:,.2f}**")
    else:
        st.info("No recent anomalies detected.")
