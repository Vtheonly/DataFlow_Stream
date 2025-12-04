FROM apache/spark-py:latest

USER root

# Pre-download Spark packages to avoid runtime download issues
RUN /opt/spark/bin/spark-submit \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.mongodb.spark:mongo-spark-connector_2.12:3.0.1 \
    --dry-run \
    --class org.apache.spark.examples.SparkPi \
    /opt/spark/examples/jars/spark-examples_2.12-3.4.0.jar 10 || true

# Ensure proper permissions
RUN mkdir -p /opt/spark/.ivy2/cache /opt/spark/work && \
    chmod -R 777 /opt/spark/.ivy2 /opt/spark/work

USER 185
