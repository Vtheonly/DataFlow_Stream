import json
import time
from twitchio.ext import commands
from aiokafka import AIOKafkaProducer

from adapters.base_stream_source import BaseStreamSource
from logic.nlp_toxicity.toxicity_classifier import ToxicityClassifier
from logic.anomaly_detection.chat_anomaly import ChatAnomalyDetector
from utils.logger import get_logger

logger = get_logger(__name__)

class TwitchChatAdapter(BaseStreamSource, commands.Bot):
    """
    Adapter for ingesting real-time chat messages from a Twitch channel.
    """
    def __init__(self, token: str, nickname: str, channel: str, producer: AIOKafkaProducer, topic: str):
        super().__init__(token=token, prefix='!', initial_channels=[channel])
        self.producer = producer
        self.topic = topic
        self.channel_name = channel
        self.nlp_classifier = ToxicityClassifier.get_instance()
        self.anomaly_detector = ChatAnomalyDetector()
        logger.info(f"TwitchChatAdapter initialized for channel: {channel}")

    async def connect(self):
        # The run method from commands.Bot handles the connection.
        pass

    async def fetch_event(self):
        # This is event-driven, handled by event_message.
        pass

    def normalize(self, message) -> dict:
        """
        Normalizes a raw Twitch message and enriches it with NLP and anomaly detection.
        """
        timestamp = time.time()
        
        # 1. Basic Normalization
        normalized_event = {
            "source": "twitch_chat",
            "type": "chat",
            "event_id": message.id,
            "timestamp": timestamp,
            "payload": {
                "author": message.author.name,
                "text": message.content,
                "channel": self.channel_name,
            }
        }

        # 2. NLP Toxicity Classification
        toxicity_scores = self.nlp_classifier.predict(message.content)
        normalized_event["enrichments"] = {"toxicity": toxicity_scores}

        # 3. Anomaly Detection
        anomaly_result = self.anomaly_detector.detect(normalized_event)
        normalized_event["enrichments"]["anomaly"] = anomaly_result
        
        return normalized_event

    async def event_ready(self):
        logger.info(f"Successfully connected to Twitch as {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return

        try:
            logger.debug(f"Received message from {message.author.name}: {message.content}")
            
            # Normalize and enrich the message
            normalized_event = self.normalize(message)
            
            # Send to Kafka
            await self.producer.send_and_wait(
                self.topic, 
                json.dumps(normalized_event).encode('utf-8')
            )
            logger.debug(f"Successfully sent enriched chat message to Kafka topic: {self.topic}")

        except Exception as e:
            logger.error(f"Error processing Twitch message: {e}", exc_info=True)

    async def run(self):
        logger.info("Starting Twitch Chat Adapter...")
        await super().run()
