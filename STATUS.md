# DataFlow Stream - System Status

## Current Status

### ✅ Services Running

- MongoDB: Running (`http://localhost:8081` for Mongo Express)
- Kafka: Running (`http://localhost:8080` for Kafka UI)
- Streamlit Dashboard: Running (`http://localhost:8501`)
- Spark Master: Running (`http://localhost:8082`)
- Spark Worker: Running
- Ingestion Service: Stable (Automatic model download enabled)

### 📊 System Health

- **Data Flow**: Active
- **NLP Model**: `unitary/toxic-bert` (Hosted by Hugging Face)
- **Latencies**: Normal

## Access Information

### MongoDB

- **Mongo Express UI**: http://localhost:8081
- **No authentication required** (development mode)
- **Direct connection**: `mongodb://localhost:27017`

### Dashboards

- **Streamlit**: http://localhost:8501
- **Kafka UI**: http://localhost:8080
- **Spark Master**: http://localhost:8082

## Monitor Progress

```bash
# Watch ingestion service logs
docker logs ingestion-service -f

# Check if data is in Kafka
docker exec kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic chat_stream --max-messages 5

# Check MongoDB collections
docker exec mongodb mongosh --quiet --eval "use DataFlowDB; show collections"
```

## Spark Job

The Spark streaming job needs to be submitted manually once data starts flowing:

```bash
docker exec -d spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.mongodb.spark:mongo-spark-connector_2.12:3.0.1 \
  /opt/spark/jobs/stream_processor.py
```
