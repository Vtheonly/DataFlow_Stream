import numpy as np
from collections import deque

class MarketAnomalyDetector:
    def __init__(self, window_size=50, z_score_threshold=3.0):
        self.window_size = window_size
        self.z_score_threshold = z_score_threshold
        self.prices = deque(maxlen=window_size)

    def detect(self, current_price: float) -> dict:
        """
        Detects anomalies based on Z-score of the current price relative to the rolling window.
        """
        if len(self.prices) < 2:
            self.prices.append(current_price)
            return {"is_anomaly": "false", "reason": "Insufficient data"}

        mean = np.mean(self.prices)
        std = np.std(self.prices)

        if std == 0:
            z_score = 0.0
        else:
            z_score = (current_price - mean) / std

        is_anomaly = abs(z_score) > self.z_score_threshold
        
        self.prices.append(current_price)

        return {
            "is_anomaly": "true" if is_anomaly else "false",
            "type": "z_score_outlier" if is_anomaly else "normal",
            "severity": str(round(float(abs(z_score)), 4)),
            "mean": str(round(float(mean), 4)),
            "std": str(round(float(std), 4)),
            "z_score": str(round(float(z_score), 4))
        }
