import json
import time
import random
import asyncio
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

    async def _run_simulator(self):
        """A fallback simulator if the Twitch connection fails."""
        logger.info("Running Twitch chat simulator.")
        sample_messages = [
            "PogChamp", "LUL", "Kappa", "This stream is awesome!", 
            "Hello world", "Spam spam spam", "Can you play simulated game?",
            "You are bad at this", "I hate you", "idiot", "stupid", # Toxic examples
            "Great play!", "GG", "EZ", "Clap", "monkaS"
        ]
        sample_authors = ["user1", "user2", "troll123", "fan456", "mod_guy"]
        
        while True:
            try:
                text = random.choice(sample_messages)
                author = random.choice(sample_authors)
                
                # Create a mock message object structure expected by normalize
                class MockMessage:
                    def __init__(self, content, author_name):
                        self.content = content
                        self.author = type('obj', (object,), {'name': author_name})
                        self.id = str(int(time.time() * 1000))
                
                mock_msg = MockMessage(text, author)
                
                # Normalize and enrich
                normalized_event = self.normalize(mock_msg)
                
                # Send to Kafka
                await self.producer.send_and_wait(
                    self.topic, 
                    json.dumps(normalized_event).encode('utf-8')
                )
                logger.debug(f"Sent simulated chat message: {text}")
                
                await asyncio.sleep(random.uniform(0.1, 0.5)) # Fast rate for "rain"
                
            except Exception as e:
                logger.error(f"Error in Twitch simulator: {e}")
                await asyncio.sleep(1)

    async def run(self):
        logger.info("Starting Twitch Chat Adapter...")
        try:
            # Attempt to connect, but if it fails or returns immediately, run simulator
            # Note: twitchio run() is blocking, so we might need to wrap it or handle failure
            # For now, we'll assume if credentials are bad, it might raise or just not work.
            # But since we want to FORCE "make it rain", let's just run the simulator if we can't connect.
            # However, twitchio.Bot.run() is a blocking call. 
            # We will try to run it, but if it fails, we catch it. 
            # Actually, to "make it rain" reliably without valid creds, maybe we should just default to simulator 
            # if the user wants it. But let's try to be robust.
            
            # If we want to support fallback, we need to handle the loop. 
            # twitchio's run() starts the loop. 
            # Let's try to start it, and if it fails, use simulator.
            await super().start()
        except Exception as e:
            logger.warning(f"Failed to connect to Twitch: {e}. Falling back to simulator.")
            await self._run_simulator()

