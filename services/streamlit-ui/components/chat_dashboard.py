import streamlit as st
import pandas as pd
from utils.mongo_client import get_chat_data, get_chat_anomalies

def display_chat_dashboard():
    st.header(" Twitch Chat Analytics")

    # Fetch data
    chat_messages = get_chat_data(limit=100)
    anomalies = get_chat_anomalies(limit=50)
    
    if not chat_messages:
        st.warning("No chat data found in the database yet.")
        return

    df_chat = pd.DataFrame(chat_messages)
    
    # --- Layout ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Live Chat Feed")
        # Display chat messages with toxicity scores
        for index, row in df_chat.iterrows():
            author = row['payload']['author']
            text = row['payload']['text']
            toxicity = row.get('enrichments', {}).get('toxicity', {})
            toxic_score = toxicity.get('toxic', 0.0)
            
            color = "gray"
            if toxic_score > 0.8: color = "red"
            elif toxic_score > 0.5: color = "orange"
            
            st.markdown(f"**{author}**: {text} `(Toxicity: {toxic_score:.2f})`", unsafe_allow_html=True)
            st.markdown(f"<hr style='margin-top:0.1rem; margin-bottom:0.1rem; border-top: 1px solid {color};'>", unsafe_allow_html=True)


    with col2:
        st.subheader("Real-Time Toxicity Alerts")
        if anomalies:
            df_anomalies = pd.DataFrame(anomalies)
            for index, row in df_anomalies.iterrows():
                anomaly_type = row['enrichments']['anomaly'].get('type', 'N/A')
                author = row['payload']['author']
                st.error(f"**{anomaly_type.replace('_', ' ').title()}**: User `{author}` triggered an alert.")
        else:
            st.info("No recent anomalies detected.")

        st.subheader("Top Toxic Users")
        # Simple aggregation for display
        df_chat['toxic_score'] = df_chat['enrichments'].apply(lambda x: x.get('toxicity', {}).get('toxic', 0.0))
        top_toxic_users = df_chat.groupby('payload.author')['toxic_score'].mean().nlargest(5)
        st.bar_chart(top_toxic_users)
