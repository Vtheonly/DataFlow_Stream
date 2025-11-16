import os
from aiokafka import AIOKafkaProducer
from utils.logger import get_logger

logger = get_logger(__name__)

async def get_kafka_producer():
    """
    Creates and returns an AIOKafkaProducer instance.
    """
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
    try:
        await producer.start()
        logger.info(f"Kafka producer connected to {bootstrap_servers}")
        return producer
    except Exception as e:
        logger.error(f"Failed to connect Kafka producer: {e}", exc_info=True)
        raise
