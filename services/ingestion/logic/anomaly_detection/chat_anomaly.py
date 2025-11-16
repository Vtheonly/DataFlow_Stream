from collections import deque, defaultdict
import time
from utils.logger import get_logger

logger = get_logger(__name__)

class ChatAnomalyDetector:
    """
    Detects anomalies in chat streams like toxicity spikes and message frequency abuse.
    """
    def __init__(self, time_window_seconds=60, toxicity_threshold=0.8, freq_threshold=10):
        self.time_window = time_window_seconds
        self.toxicity_threshold = toxicity_threshold
        self.freq_threshold = freq_threshold
        
        self.message_timestamps = deque()
        self.user_message_counts = defaultdict(lambda: deque())

    def detect(self, event: dict) -> dict:
        result = {"is_anomaly": False, "type": None, "details": {}}
        current_time = event["timestamp"]
        
        # 1. Toxicity Spike Detection
        toxic_score = event.get("enrichments", {}).get("toxicity", {}).get("toxic", 0.0)
        if toxic_score > self.toxicity_threshold:
            result = {
                "is_anomaly": True,
                "type": "toxicity_spike",
                "details": {"user": event["payload"]["author"], "score": toxic_score}
            }

        # 2. Message Frequency Anomaly (Spam) Detection per user
        author = event["payload"]["author"]
        user_deque = self.user_message_counts[author]
        user_deque.append(current_time)
        
        # Remove old timestamps from the user's deque
        while user_deque and user_deque[0] < current_time - self.time_window:
            user_deque.popleft()
            
        if len(user_deque) > self.freq_threshold:
            result = {
                "is_anomaly": True,
                "type": "frequency_spam",
                "details": {"user": author, "count_in_window": len(user_deque)}
            }
            
        return result
