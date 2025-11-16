import asyncio
import os
from dotenv import load_dotenv

from adapters.twitch_chat_adapter import TwitchChatAdapter
from adapters.market_adapter import MarketAdapter
from utils.kafka_producer import get_kafka_producer
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

async def main():
    """
    IngestionOrchestrator: Initializes and runs all data stream adapters concurrently.
    """
    logger.info("Initializing Ingestion Orchestrator...")
    producer = await get_kafka_producer()

    # --- Configuration ---
    twitch_oauth = os.getenv("TWITCH_OAUTH_TOKEN")
    twitch_nick = os.getenv("TWITCH_NICKNAME")
    twitch_channel = os.getenv("TWITCH_CHANNEL")
    market_symbol = os.getenv("MARKET_SYMBOL")
    
    chat_topic = os.getenv("CHAT_KAFKA_TOPIC")
    market_topic = os.getenv("MARKET_KAFKA_TOPIC")

    # --- Initialize Adapters ---
    twitch_adapter = TwitchChatAdapter(
        token=twitch_oauth,
        nickname=twitch_nick,
        channel=twitch_channel,
        producer=producer,
        topic=chat_topic
    )
    
    market_adapter = MarketAdapter(
        symbol=market_symbol,
        producer=producer,
        topic=market_topic
    )

    logger.info("Starting all data stream adapters...")
    
    # Run adapters concurrently
    await asyncio.gather(
        twitch_adapter.run(),
        market_adapter.run()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Ingestion service shutting down.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the orchestrator: {e}", exc_info=True)
