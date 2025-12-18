import json
import time
import random
import asyncio
import websockets
import re
from aiokafka import AIOKafkaProducer

from adapters.base_stream_source import BaseStreamSource
from logic.nlp_toxicity.toxicity_classifier import ToxicityClassifier
from logic.anomaly_detection.chat_anomaly import ChatAnomalyDetector
from utils.logger import get_logger

logger = get_logger(__name__)

class TwitchChatAdapter(BaseStreamSource):
    """
    Adapter for ingesting real-time chat messages via Raw WebSockets.
    Bypasses twitchio library to avoid event loop conflicts.
    """
    def __init__(self, token: str, nickname: str, channel: str, producer: AIOKafkaProducer, topic: str):
        self.token = token if token.startswith("oauth:") else f"oauth:{token}"
        self.nickname = nickname.lower()
        self.channel = f"#{channel.lower().lstrip('#')}"
        self.producer = producer
        self.topic = topic
        
        self.uri = "wss://irc-ws.chat.twitch.tv:443"
        self.nlp_classifier = ToxicityClassifier.get_instance()
        self.anomaly_detector = ChatAnomalyDetector()
        logger.info(f"TwitchChatAdapter (Raw WS) initialized for channel: {self.channel}")

    async def connect(self):
        try:
            websocket = await websockets.connect(self.uri)
            
            # Authenticate
            await websocket.send(f"PASS {self.token}")
            await websocket.send(f"NICK {self.nickname}")
            
            # Join Channel
            await websocket.send(f"JOIN {self.channel}")
            
            logger.info(f"✅ Successfully connected to Twitch IRC as {self.nickname}")
            return websocket
        except Exception as e:
            logger.error(f"Failed to connect to Twitch IRC: {e}")
            raise

    async def fetch_event(self):
        pass

    def normalize(self, raw_message, author) -> dict:
        timestamp = time.time()
        normalized_event = {
            "source": "twitch_chat",
            "type": "chat",
            "event_id": str(timestamp),
            "timestamp": timestamp,
            "payload": {
                "author": author,
                "text": raw_message,
                "channel": self.channel,
            }
        }
        
        # NLP Enrichment
        toxicity_scores = self.nlp_classifier.predict(raw_message)
        normalized_event["enrichments"] = {"toxicity": toxicity_scores}

        # Anomaly Detection
        anomaly_result = self.anomaly_detector.detect(normalized_event)
        normalized_event["enrichments"]["anomaly"] = anomaly_result
        
        return normalized_event

    async def _run_simulator(self):
        logger.info("Running Twitch chat simulator.")
        sample_messages = ["PogChamp", "LUL", "Kappa", "This stream is awesome!", "Hello world"]
        sample_authors = ["user1", "user2", "troll123", "fan456"]
        
        while True:
            text = random.choice(sample_messages)
            author = random.choice(sample_authors)
            
            normalized_event = self.normalize(text, author)
            await self.producer.send_and_wait(self.topic, json.dumps(normalized_event).encode('utf-8'))
            await asyncio.sleep(1)

    async def run(self):
        logger.info(f"Starting Twitch Chat Adapter (Raw WebSocket Mode) for {self.channel}...")
        while True:
            try:
                # Use context manager for auto-cleanup and better stability
                async with websockets.connect(self.uri) as websocket:
                    # Authenticate
                    await websocket.send(f"PASS {self.token}")
                    await websocket.send(f"NICK {self.nickname}")
                    # Request capabilities for full message visibility
                    await websocket.send("CAP REQ :twitch.tv/membership twitch.tv/tags twitch.tv/commands")
                    await websocket.send(f"JOIN {self.channel}")
                    
                    logger.info(f"✅ Connected and joined {self.channel}")
                    
                    while True:
                        try:
                            # Use timeout to detect dead connections
                            data = await asyncio.wait_for(websocket.recv(), timeout=30)
                            if isinstance(data, bytes):
                                data = data.decode('utf-8')
                            
                            for message in data.split('\r\n'):
                                message = message.strip()
                                if not message:
                                    continue
                                    
                                logger.debug(f"RAW IRC: {message}")
                                
                                # Keep Alive
                                if message.startswith("PING"):
                                    await websocket.send("PONG :tmi.twitch.tv")
                                    logger.debug("✅ Sent PONG to Twitch")
                                    continue

                                # Robust Twitch IRC Parser
                                # Format: [@tags] :prefix COMMAND [params] [:trailing]
                                irc_msg = message
                                
                                # 1. Extract Tags
                                tags = {}
                                if irc_msg.startswith("@"):
                                    tags_str, irc_msg = irc_msg.split(" ", 1)
                                
                                # 2. Extract Prefix
                                if irc_msg.startswith(":"):
                                    prefix, irc_msg = irc_msg[1:].split(" ", 1)
                                    username = prefix.split("!", 1)[0]
                                else:
                                    username = "system"

                                # 3. Handle PRIVMSG
                                if "PRIVMSG" in irc_msg:
                                    # Format: #channel :message content
                                    try:
                                        params, content = irc_msg.split("PRIVMSG ", 1)[1].split(" :", 1)
                                        channel = params.strip()
                                        
                                        logger.info(f"Received from {username}: {content}")
                                        
                                        # Normalize and Send
                                        event = self.normalize(content, username)
                                        await self.producer.send_and_wait(self.topic, json.dumps(event).encode('utf-8'))
                                        logger.debug(f"Successfully sent enriched chat message to Kafka.")
                                    except Exception as parse_e:
                                        logger.debug(f"Parsing PRIVMSG failed: {parse_e}")

                                elif "JOIN" in irc_msg:
                                    logger.debug(f"System: {username} joined channel.")
                        except asyncio.TimeoutError:
                            logger.info("Socket Timeout (30s) - actively probing with PING")
                            await websocket.send("PING :tmi.twitch.tv")
                        except Exception as inner_e:
                            logger.error(f"Error in message loop: {inner_e}")
                            break

            except Exception as e:
                logger.warning(f"Connection lost or failed: {e}. Retrying in 5s...")
                await asyncio.sleep(5)