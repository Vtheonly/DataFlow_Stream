import asyncio
import json
import time
import random
import websockets
from aiokafka import AIOKafkaProducer

from adapters.base_stream_source import BaseStreamSource
from logic.anomaly_detection.market_anomaly import MarketAnomalyDetector
from utils.logger import get_logger

logger = get_logger(__name__)
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@trade"

class MarketAdapter(BaseStreamSource):
    """
    Adapter for ingesting real-time market trade data.
    Uses a real Binance WebSocket but includes a simulator as a fallback.
    """
    def __init__(self, symbol: str, producer: AIOKafkaProducer, topic: str):
        self.symbol = symbol.lower()
        self.producer = producer
        self.topic = topic
        self.anomaly_detector = MarketAnomalyDetector()
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@trade"
        logger.info(f"MarketAdapter initialized for symbol: {self.symbol}")

    async def connect(self):
        try:
            websocket = await websockets.connect(self.ws_url)
            logger.info(f"Successfully connected to Binance WebSocket at {self.ws_url}")
            return websocket
        except Exception as e:
            logger.warning(f"Failed to connect to real WebSocket: {e}. Falling back to simulator.")
            return None

    async def fetch_event(self):
        # This is handled within the run loop.
        pass

    def normalize(self, raw_event: dict) -> dict:
        """
        Normalizes a raw market trade event and runs anomaly detection.
        """
        timestamp = time.time()
        
        # 1. Basic Normalization
        normalized_event = {
            "source": "market_data",
            "type": "trade",
            "event_id": raw_event.get('t'),
            "timestamp": timestamp,
            "payload": {
                "symbol": raw_event.get('s'),
                "price": float(raw_event.get('p')),
                "quantity": float(raw_event.get('q')),
            }
        }

        # 2. Anomaly Detection
        anomaly_result = self.anomaly_detector.detect(normalized_event['payload']['price'])
        normalized_event["enrichments"] = {"anomaly": anomaly_result}
        
        return normalized_event

    async def _run_simulator(self):
        """A fallback simulator if the WebSocket connection fails."""
        logger.info("Running market data simulator.")
        current_price = 65000.0
        while True:
            price_change = random.uniform(-100, 100)
            # Occasionally create a large jump for anomaly detection
            if random.random() < 0.05:
                price_change *= 10
            
            current_price += price_change
            
            simulated_event = {
                's': self.symbol.upper(),
                'p': f"{current_price:.2f}",
                'q': f"{random.uniform(0.01, 1.0):.4f}",
                't': int(time.time() * 1000)
            }
            
            normalized_event = self.normalize(simulated_event)
            await self.producer.send_and_wait(
                self.topic,
                json.dumps(normalized_event).encode('utf-8')
            )
            logger.debug("Sent simulated market event to Kafka.")
            await asyncio.sleep(1)

    async def run(self):
        logger.info("Starting Market Data Adapter...")
        websocket = await self.connect()
        if not websocket:
            await self._run_simulator()
            return
            
        while True:
            try:
                raw_data = await websocket.recv()
                raw_event = json.loads(raw_data)
                
                logger.debug(f"Received market data: {raw_event}")
                
                normalized_event = self.normalize(raw_event)
                await self.producer.send_and_wait(
                    self.topic,
                    json.dumps(normalized_event).encode('utf-8')
                )
                logger.debug(f"Successfully sent enriched market event to Kafka topic: {self.topic}")
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed. Reconnecting...")
                websocket = await self.connect()
                if not websocket:
                    await self._run_simulator()
                    return
            except Exception as e:
                logger.error(f"Error in market adapter loop: {e}", exc_info=True)
                await asyncio.sleep(5)