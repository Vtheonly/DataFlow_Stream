import os
from pymongo import MongoClient

class MongoSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
            try:
                cls._instance = MongoClient(mongo_uri)
            except Exception as e:
                print(f"Failed to connect to MongoDB: {e}")
                raise
        return cls._instance

def get_db():
    client = MongoSingleton.get_instance()
    db_name = os.getenv("MONGO_DATABASE", "DataFlowDB")
    return client[db_name]

# --- Data Fetching Functions ---

def get_chat_data(limit=100):
    db = get_db()
    return list(db.enriched_events.find({"source": "twitch_chat"}).sort("_id", -1).limit(limit))

def get_market_data(limit=200):
    db = get_db()
    return list(db.enriched_events.find({"source": "market_data"}).sort("_id", -1).limit(limit))

def get_chat_anomalies(limit=50):
    db = get_db()
    return list(db.chat_anomalies.find().sort("_id", -1).limit(limit))

def get_market_anomalies(limit=50):
    db = get_db()
    return list(db.market_anomalies.find().sort("_id", -1).limit(limit))

def get_db_stats():
    db = get_db()
    return {
        "enriched_events": db.enriched_events.count_documents({}),
        "chat_messages": db.enriched_events.count_documents({"source": "twitch_chat"}),
        "market_trades": db.enriched_events.count_documents({"source": "market_data"}),
        "chat_anomalies": db.chat_anomalies.count_documents({}),
        "market_anomalies": db.market_anomalies.count_documents({}),
    }
