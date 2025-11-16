# DataFlow Stream: Real-Time Data Processing Pipeline

This project is a complete, production-ready real-time data processing pipeline designed to ingest, process, analyze, and visualize data from multiple sources like Twitch chat and financial markets.

## Tech Stack

- **Data Ingestion**: Python, Websockets
- **Streaming Platform**: Apache Kafka
- **Real-Time Processing**: Apache Spark (Structured Streaming)
- **Database**: MongoDB
- **Dashboard/UI**: Streamlit
- **Orchestration**: Docker Compose
- **NLP**: Keras/TensorFlow

## Features

- **Multi-Source Ingestion**: Unified adapter pattern to connect to Twitch chat, market data streams, and more.
- **Real-Time NLP**: Live toxicity analysis on chat messages.
- **Real-Time Anomaly Detection**: Z-score and volatility spike detection for market data; toxicity and frequency anomaly detection for chat data.
- **End-to-End Streaming**: A fully containerized pipeline from data source to dashboard.
- **Live Monitoring**: A Streamlit dashboard visualizes live data, toxicity scores, market anomalies, and system health.

## How to Run

1.  **Prerequisites**:
    - Docker and Docker Compose installed.
    - Python 3.9+

2.  **Configuration**:
    - Copy `.env.local` to a new file named `.env.development`.
    - Fill in the required environment variables:
      - `TWITCH_OAUTH_TOKEN`: Your Twitch OAuth token.
      - `TWITCH_NICKNAME`: Your Twitch nickname.
      - `TWITCH_CHANNEL`: The Twitch channel to monitor.

3.  **Build and Run**:
    ```bash
    docker-compose up --build
    ```

4.  **Access Services**:
    - **Streamlit Dashboard**: `http://localhost:8501`
    - **Kafka UI**: `http://localhost:8080`
    - **Mongo Express**: `http://localhost:8081`

## Architecture

The system is composed of several microservices orchestrated by Docker Compose.

1.  **Ingestion Service**: A Python service that connects to data sources (Twitch, Binance), normalizes the data, runs NLP and anomaly detection, and produces events to Kafka topics.
2.  **Kafka Cluster**: Acts as the central data bus for all real-time events.
3.  **Spark Cluster**: Consumes data from Kafka, performs stateful aggregations and transformations, and writes results to MongoDB.
4.  **MongoDB**: Stores the raw and enriched data for querying by the dashboard.
5.  **Streamlit UI**: A Python web application that queries MongoDB to provide a real-time visualization of the pipeline's data.