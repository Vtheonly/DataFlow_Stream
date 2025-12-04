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



Below is the **full, deep, end-to-end explanation** of everything you are building.
This is the “from scratch, understand every component, understand the workflow, understand each feature, and understand what the final system does” version.

I will not simplify; I will explain it the way an engineer designing a real production streaming architecture would.

I will walk through:

1. What the full project is
2. Why each part exists
3. What each part does
4. How data flows from start to finish
5. How the system behaves in production
6. What your final result looks like
7. What each component’s responsibilities are
8. What features actually provide value

This will be **long, layered, precise, and deeply technical**.

---

# THE FULL SYSTEM: What You Are Actually Building

You are building an **industrial-grade real-time data processing pipeline**.
Think of it as a mini version of what Twitch, TikTok, Binance, or Netflix use internally:

**DataFlow Stream: A unified system that ingests, analyzes, enriches, detects anomalies, stores, and visualizes data in real time.**

It handles *two* streaming sources:

1. **Twitch live chat**
2. **Market price streams**

Everything is modular, meaning it can ingest more sources later.

The system performs:

* real-time ingestion
* normalization
* NLP toxicity detection
* anomaly detection
* structured streaming analytics
* persistence
* real-time dashboards

And everything runs in *distributed microservices* under **Docker Compose.**

---

# OVERVIEW OF THE ARCHITECTURE

Here is the global workflow, end-to-end:

```
Twitch Chat → Twitch Adapter
                      ↓
Market Data → Market Adapter
                      ↓
            Unified Normalization Layer
                      ↓
    NLP Toxicity + Anomaly Detection Layer
                      ↓
                  Kafka Producers
                      ↓
               Kafka Distributed Log
                      ↓
             Spark Structured Streaming
                      ↓
         Enriched + Analysed Data Output
                      ↓
                  MongoDB Storage
                      ↓
            Streamlit Real-Time Dashboard
```

Under the hood, Kafka depends on **Zookeeper** for cluster coordination.

---

# THE WORKFLOW: START TO FINISH

## 1. Real-Time Ingestion Layer

This layer is built using pure Python and OOP design.

### Components:

### 1. BaseStreamSource

A parent class enforcing:

* connect()
* read()
* close()
* error handling
* message format consistency

It defines the interface so all adapters behave identically.

---

### 2. TwitchChatAdapter

This component:

* connects to Twitch API or IRC WebSocket
* receives every message the moment it appears
* extracts useful fields:

  * username
  * message
  * timestamp
  * channel
  * metadata

It converts raw Twitch messages into a structured Python dict.

---

### 3. MarketAdapter

This connects to a crypto exchange stream (Binance, Coinbase, or simulated).

It ingests:

* price
* volume
* market direction
* timestamp

Every tick becomes a structured event.

---

### 4. Unified Normalization Layer

All incoming events—whether from Twitch or market streams—are converted into a **single universal schema**, for example:

```
{
  "source": "twitch" | "market",
  "timestamp": ...,
  "payload": {
       ... raw data normalized ...
  }
}
```

This is essential because:

* Kafka expects consistent formats
* Spark needs structured input
* MongoDB prefers predictable schemas
* your dashboard can treat all streams uniformly

This is how you build *extensible* software.

---

## 2. NLP Toxicity Detection Layer

Every Twitch message goes through your NLP toxic-language classifier.

### What it does:

* loads a trained Keras model
* loads a tokenizer
* processes text
* predicts several labels:

  * toxic
  * severe toxic
  * insult
  * threat
  * obscene

### Why this matters:

Real-time chat analysis becomes possible:

* block toxic users
* detect chat raids
* measure community health
* flag suspicious accounts

Every message gets a **toxicity score** before it reaches Kafka.

---

## 3. Anomaly Detection Layer

This handles both chat and market anomalies.

### Market anomalies:

* sudden jumps
* volatility spikes
* abnormal volume
* deviation from rolling mean
* z-score outliers

### Twitch anomalies:

* message rate spikes
* coordinated spam
* high toxicity bursts
* repeating patterns
* bot detection

This layer annotates each event with anomaly metadata.

Output example:

```
{
  ...,
  "anomaly": {
      "isAnomaly": true,
      "type": "volatility_spike",
      "severity": 0.82
  }
}
```

---

## 4. Kafka Layer

Kafka is the **distributed messaging backbone**.

### What Kafka does:

* receives events from the ingestion layer
* partitions them
* acts as a durable, scalable log
* allows Spark, monitoring, archival systems to consume simultaneously

### Topics:

* `chat_stream`
* `market_stream`
* `analytics_stream`

### Why Kafka matters:

Without Kafka, you cannot do scalable real-time architecture.
Kafka is the **buffer between ingestion and analytics**, preventing overload.

---

## 5. Zookeeper

Zookeeper manages Kafka’s cluster consistency:

* elects leaders
* tracks broker health
* stores metadata
* ensures failover
* coordinates partitions

Kafka does **not** work without Zookeeper (unless using KRaft, which we will not).

---

## 6. Spark Structured Streaming

Spark is the system’s real-time brain.

### What Spark does:

* consumes Twitch and market streams from Kafka
* parses JSON
* executes structured transformations
* computes rolling windows
* aggregates metrics
* performs secondary anomaly detection
* enriches events
* outputs results to MongoDB and Kafka

Spark is the heavy-duty analytics engine.

### Example tasks:

* top toxic users last 10 seconds
* average market price every 1 second
* detect conversation sentiment trend
* detect volatility behavior
* side-stream alerts

Spark is what makes your project feel **enterprise-level**.

---

## 7. MongoDB Layer

MongoDB stores everything:

### Collections:

* raw_events
* enriched_events
* market_anomalies
* chat_toxicity
* alerts

### Why MongoDB?

Because it is perfect for:

* unstructured data
* fast reads
* dashboards
* flexible schemas

Mongo is what your dashboard queries.

---

## 8. Streamlit Dashboard

This is your user interface.

### What it shows:

#### Twitch Module

* live chat feed (auto-updating)
* toxicity timeline
* top toxic users
* chat spike anomalies

#### Market Module

* live price chart
* anomaly markers
* volatility indicators
* alert timeline

#### System Module

* Kafka metrics
* Spark streaming throughput
* ingestion performance
* cluster health

Streamlit is Python-native, reactive, simple, and dynamic.

---

## 9. Docker and DevOps Layer

Everything runs in containers:

* Zookeeper
* Kafka
* Spark master
* Spark workers
* MongoDB
* Mongo Express
* NLP Service
* Ingestion Service
* Streamlit UI

### Docker Compose orchestrates:

* networking
* service dependencies
* environment variables
* scaling
* restarts

This is what makes your system **production-grade**.

---

# WHAT YOUR FINAL SYSTEM LOOKS LIKE

At the end, you will have:

### A fully integrated multi-service distributed pipeline that:

* ingests live Twitch chat in real time
* ingests live market data in real time
* normalizes all events
* applies NLP toxicity detection
* applies anomaly detection
* publishes everything to Kafka
* processes data with Spark
* stores results in MongoDB
* presents them in a Streamlit dashboard
* all containerized and ready for deployment

### You can run one command:

```
docker compose up --build
```

And suddenly you have:

* real-time dashboards
* machine learning pipelines
* distributed messaging
* analytics
* anomaly detection
* fully logged, monitored, engineered infrastructure

This is the same architecture major streaming companies use.

---

# WHAT EACH FEATURE DOES (SUMMARY)

### Twitch Adapter

Extracts and normalizes Twitch messages.

### Market Adapter

Streams real-time market prices.

### NLP Toxicity Module

Tags toxic/harmful chat messages.

### Anomaly Detection

Flags strange activity in chat and markets.

### Kafka

Scalable real-time event backbone.

### Zookeeper

Cluster coordination for Kafka.

### Spark Streaming

Continuous real-time analytics engine.

### MongoDB

Stores raw + enriched + anomaly + dashboard data.

### Streamlit Dashboard

Visual UI for everything happening in real time.

### Docker Compose

Runs all services automatically in a cluster.

---

# If you want the *same depth* for:

* folder structure overview
* exact deployment flow
* testing strategy
* scaling strategy
* monitoring design
* logging architecture
* extension to multiple channels
* or a full PDF-style documentation

I can generate that too.
