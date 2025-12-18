import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.mongo_client import get_chat_data, get_chat_anomalies, get_db_stats

def display_chat_dashboard():
    st.header("Twitch Chat Analytics")

    # Fetch data
    chat_messages = get_chat_data(limit=100)
    anomalies = get_chat_anomalies(limit=50)
    stats = get_db_stats()
    
    if not chat_messages:
        st.info("Waiting for processed chat data... (Spark job might be initializing)")
        st.caption("Common causes: Spark is downloading dependencies or Twitch channel is currently quiet.")
        return

    df_chat = pd.DataFrame(chat_messages)
    
    # Extract nested fields
    df_chat['author'] = df_chat['payload'].apply(lambda x: x.get('author', 'Unknown'))
    df_chat['text'] = df_chat['payload'].apply(lambda x: x.get('text', ''))
    df_chat['toxic_score'] = df_chat['enrichments'].apply(lambda x: x.get('toxicity', {}).get('toxic', 0.0))
    df_chat['severe_toxic'] = df_chat['enrichments'].apply(lambda x: x.get('toxicity', {}).get('severe_toxic', 0.0))
    df_chat['insult'] = df_chat['enrichments'].apply(lambda x: x.get('toxicity', {}).get('insult', 0.0))
    
    # --- Stats Row ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Messages (DB)", stats.get('chat_messages', 0))
    col2.metric("Chat Anomalies", stats.get('chat_anomalies', 0))
    col3.metric("Avg Toxicity (Batch)", f"{df_chat['toxic_score'].mean():.4f}")
    col4.metric("Max Toxicity (Batch)", f"{df_chat['toxic_score'].max():.4f}")
    
    st.divider()
    
    # --- Layout ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Live Chat Feed")
        # Display chat messages with toxicity scores
        for index, row in df_chat.head(15).iterrows():
            author = row['author']
            text = row['text']
            toxic_score = row['toxic_score']
            
            score_label = f" (Toxic: {toxic_score:.2f})"
            
            if toxic_score > 0.8:
                st.markdown(f"**{author}**: {text} <span style='color: #ff4b4b; font-size: 0.8em;'>{score_label}</span>", unsafe_allow_html=True)
            elif toxic_score > 0.5:
                st.markdown(f"**{author}**: {text} <span style='color: #ffa500; font-size: 0.8em;'>{score_label}</span>", unsafe_allow_html=True)
            elif toxic_score > 0.2:
                st.markdown(f"**{author}**: {text} <span style='color: #ffff00; font-size: 0.8em;'>{score_label}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"**{author}**: {text} <span style='color: #00ff00; font-size: 0.8em;'>{score_label}</span>", unsafe_allow_html=True)

    with col2:
        st.subheader("Toxicity Alerts")
        if anomalies:
            for a in anomalies[:5]:
                anomaly_type = a.get('enrichments', {}).get('anomaly', {}).get('type', 'N/A')
                author = a.get('payload', {}).get('author', 'Unknown')
                st.error(f"**{anomaly_type}**: `{author}`")
        else:
            st.info("No recent anomalies detected.")

    st.divider()
    
    # --- Charts ---
    st.subheader("Scalable Analytics")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Top Toxic Users (Limited to Top 10)
        st.write("**Top 10 Most Toxic Users**")
        top_users = df_chat.groupby('author')['toxic_score'].mean().nlargest(10).reset_index()
        fig = px.bar(top_users, x='author', y='toxic_score', 
                     color='toxic_score', color_continuous_scale='Reds',
                     labels={'toxic_score': 'Avg Toxicity', 'author': 'User'})
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        # Message Count by User (Top 5 + Other)
        st.write("**Activity Distribution (Top 5 vs Others)**")
        msg_counts = df_chat['author'].value_counts()
        top_5 = msg_counts.head(5)
        others = pd.Series({'Other Users': msg_counts.iloc[5:].sum()}) if len(msg_counts) > 5 else pd.Series()
        final_counts = pd.concat([top_5, others]).reset_index()
        final_counts.columns = ['User', 'Messages']
        
        fig3 = px.pie(final_counts, values='Messages', names='User', hole=0.4,
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig3, use_container_width=True)
