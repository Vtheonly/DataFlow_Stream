import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.mongo_client import get_market_data, get_market_anomalies

def display_market_dashboard():
    st.header("Market Analytics")

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

    # --- Metrics and Z-score Analytics ---
    st.subheader("Market Statistics & Z-Score")
    
    # Extract metrics from recent data if available
    latest_z = 0.0
    latest_mean = 0.0
    latest_std = 0.0
    
    # Try to find the latest anomaly or detail from recent data
    if anomalies:
        latest = anomalies[0]
        latest_z = float(latest['enrichments']['anomaly'].get('z_score', 0.0))
        latest_mean = float(latest['enrichments']['anomaly'].get('mean', 0.0))
        latest_std = float(latest['enrichments']['anomaly'].get('std', 0.0))

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Z-Score", f"{latest_z:.2f}", delta=f"{latest_z:.2f}", delta_color="inverse")
    col2.metric("Rolling Mean", f"${latest_mean:,.2f}")
    col3.metric("Rolling StdDev", f"{latest_std:.2f}")

    # --- Z-Score History Chart ---
    if anomalies:
        df_anom = pd.DataFrame(anomalies)
        df_anom['timestamp'] = pd.to_datetime(df_anom['timestamp'], unit='s')
        df_anom['z_score'] = df_anom['enrichments'].apply(lambda x: float(x.get('anomaly', {}).get('z_score', 0.0)))
        
        fig_z = go.Figure()
        fig_z.add_trace(go.Scatter(
            x=df_anom['timestamp'],
            y=df_anom['z_score'],
            mode='lines+markers',
            name='Z-Score',
            line=dict(color='orange')
        ))
        # Add threshold lines
        fig_z.add_hline(y=3.0, line_dash="dash", line_color="red", annotation_text="Upper Threshold")
        fig_z.add_hline(y=-3.0, line_dash="dash", line_color="red", annotation_text="Lower Threshold")
        
        fig_z.update_layout(title="Z-Score History (Price Volatility)", xaxis_title="Time", yaxis_title="Z-Score")
        st.plotly_chart(fig_z, use_container_width=True)

    # --- Anomaly Feed ---
    st.subheader("Recent Market Anomaly Alerts")
    if anomalies:
        for anomaly in anomalies[:10]:
            anom_info = anomaly['enrichments']['anomaly']
            anomaly_type = anom_info.get('type', 'N/A').replace('_', ' ').title()
            price = anomaly['payload']['price']
            z_val = float(anom_info.get('z_score', 0.0))
            
            st.error(f"**{anomaly_type}**: Price **${price:,.2f}** (Z-Score: **{z_val:.2f}**)")
    else:
        st.info("No recent anomalies detected.")
