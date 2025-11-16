#!/bin/bash

/opt/bitnami/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.mongodb.spark:mongo-spark-connector_2.12:3.0.1 \
  /opt/bitnami/spark/jobs/stream_processor.py