import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType, MapType

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "DataFlowDB")
CHAT_TOPIC = os.getenv("CHAT_KAFKA_TOPIC", "chat_stream")
MARKET_TOPIC = os.getenv("MARKET_KAFKA_TOPIC", "market_stream")

# --- Schemas ---
CHAT_SCHEMA = StructType([
    StructField("source", StringType(), True),
    StructField("timestamp", DoubleType(), True),
    StructField("payload", StructType([
        StructField("author", StringType(), True),
        StructField("text", StringType(), True),
    ])),
    StructField("enrichments", StructType([
        StructField("toxicity", MapType(StringType(), DoubleType()), True),
        StructField("anomaly", MapType(StringType(), StringType()), True), # Anomaly details are mixed type, handle as string map
    ]))
])

MARKET_SCHEMA = StructType([
    StructField("source", StringType(), True),
    StructField("timestamp", DoubleType(), True),
    StructField("payload", StructType([
        StructField("symbol", StringType(), True),
        StructField("price", DoubleType(), True),
        StructField("quantity", DoubleType(), True),
    ])),
    StructField("enrichments", StructType([
        StructField("anomaly", MapType(StringType(), StringType()), True),
    ]))
])

def create_spark_session():
    """Creates and configures a SparkSession."""
    return (
        SparkSession.builder.appName("DataFlowStreamProcessor")
        .config("spark.mongodb.output.uri", f"{MONGO_URI}{MONGO_DATABASE}")
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.mongodb.spark:mongo-spark-connector_2.12:3.0.1")
        .getOrCreate()
    )

def process_stream(df, schema, collection_name):
    """General function to process a Kafka stream and write to MongoDB."""
    # Deserialize JSON from Kafka
    parsed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

    # Write raw enriched data to a general collection
    query = (
        parsed_df.writeStream
        .foreachBatch(lambda batch_df, batch_id: batch_df.write.format("mongo").mode("append").option("collection", "enriched_events").save())
        .start()
    )

    # Filter for anomalies and write to a specific anomaly collection
    anomaly_df = parsed_df.filter(col("enrichments.anomaly.is_anomaly") == "true")
    anomaly_query = (
        anomaly_df.writeStream
        .foreachBatch(lambda batch_df, batch_id: batch_df.write.format("mongo").mode("append").option("collection", collection_name).save())
        .start()
    )
    
    return [query, anomaly_query]

def main():
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    print("Starting Spark Streaming Processor...")

    # --- Read from Kafka Topics ---
    chat_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", CHAT_TOPIC)
        .load()
    )

    market_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", MARKET_TOPIC)
        .load()
    )

    # --- Process Streams ---
    chat_queries = process_stream(chat_df, CHAT_SCHEMA, "chat_anomalies")
    market_queries = process_stream(market_df, MARKET_SCHEMA, "market_anomalies")

    # Await termination for all queries
    for q in chat_queries + market_queries:
        q.awaitTermination()

if __name__ == "__main__":
    main()