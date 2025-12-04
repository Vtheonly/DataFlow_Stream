import os
from pymongo import MongoClient
from utils.logger import get_logger

logger = get_logger(__name__)

_client = None
_db = None

def get_mongo_client():
    global _client, _db
    if _client is None:
        mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
        db_name = os.getenv("MONGO_DATABASE", "DataFlowDB")
        _client = MongoClient(mongo_uri)
        _db = _client[db_name]
        logger.info(f"Connected to MongoDB: {db_name}")
    return _db

def save_event(event: dict):
    """Save an enriched event directly to MongoDB."""
    try:
        db = get_mongo_client()
        db.enriched_events.insert_one(event)
        
        # Also save to specific anomaly collection if applicable
        source = event.get("source", "")
        anomaly = event.get("enrichments", {}).get("anomaly", {})
        is_anomaly = anomaly.get("is_anomaly", anomaly.get("isAnomaly", "False"))
        
        if is_anomaly in [True, "True", "true"]:
            if source == "twitch_chat":
                db.chat_anomalies.insert_one(event)
            elif source == "market_data":
                db.market_anomalies.insert_one(event)
    except Exception as e:
        logger.error(f"Error saving to MongoDB: {e}")
