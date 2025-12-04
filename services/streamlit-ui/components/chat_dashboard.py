import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.mongo_client import get_chat_data, get_chat_anomalies, get_db_stats

def display_chat_dashboard():
    st.header("💬 Twitch Chat Analytics")

    # Fetch data
    chat_messages = get_chat_data(limit=100)
    anomalies = get_chat_anomalies(limit=50)
    stats = get_db_stats()
    
    if not chat_messages:
        st.warning("No chat data found in the database yet.")
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
    col1.metric("Total Messages", stats.get('chat_messages', 0))
    col2.metric("Chat Anomalies", stats.get('chat_anomalies', 0))
    col3.metric("Avg Toxicity", f"{df_chat['toxic_score'].mean():.4f}")
    col4.metric("Max Toxicity", f"{df_chat['toxic_score'].max():.4f}")
    
    st.divider()
    
    # --- Layout ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📝 Live Chat Feed")
        # Display chat messages with toxicity scores
        for index, row in df_chat.head(20).iterrows():
            author = row['author']
            text = row['text']
            toxic_score = row['toxic_score']
            
            if toxic_score > 0.8:
                st.markdown(f"🔴 **{author}**: {text} `(Toxicity: {toxic_score:.2f})`")
            elif toxic_score > 0.5:
                st.markdown(f"🟠 **{author}**: {text} `(Toxicity: {toxic_score:.2f})`")
            elif toxic_score > 0.2:
                st.markdown(f"🟡 **{author}**: {text} `(Toxicity: {toxic_score:.2f})`")
            else:
                st.markdown(f"🟢 **{author}**: {text} `(Toxicity: {toxic_score:.2f})`")

    with col2:
        st.subheader("⚠️ Toxicity Alerts")
        if anomalies:
            for a in anomalies[:5]:
                anomaly_type = a.get('enrichments', {}).get('anomaly', {}).get('type', 'N/A')
                author = a.get('payload', {}).get('author', 'Unknown')
                st.error(f"**{anomaly_type}**: `{author}`")
        else:
            st.info("No recent anomalies detected.")

    st.divider()
    
    # --- Charts ---
    st.subheader("📊 Analytics")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Top Toxic Users
        st.write("**Top Toxic Users**")
        top_users = df_chat.groupby('author')['toxic_score'].mean().nlargest(5).reset_index()
        fig = px.bar(top_users, x='author', y='toxic_score', 
                     color='toxic_score', color_continuous_scale='Reds',
                     title='Average Toxicity by User')
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        # Toxicity Distribution
        st.write("**Toxicity Distribution**")
        fig2 = px.histogram(df_chat, x='toxic_score', nbins=20,
                           title='Distribution of Toxicity Scores',
                           color_discrete_sequence=['#FF6B6B'])
        st.plotly_chart(fig2, use_container_width=True)
    
    # Messages per user
    st.write("**Message Count by User**")
    msg_count = df_chat['author'].value_counts().reset_index()
    msg_count.columns = ['author', 'count']
    fig3 = px.pie(msg_count, values='count', names='author', title='Messages by User')
    st.plotly_chart(fig3, use_container_width=True)
