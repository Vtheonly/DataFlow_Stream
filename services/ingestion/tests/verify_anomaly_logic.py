import sys
import os

# Add services/ingestion to path
sys.path.append(os.path.join(os.getcwd(), 'services/ingestion'))

from logic.anomaly_detection.chat_anomaly import ChatAnomalyDetector
from logic.anomaly_detection.market_anomaly import MarketAnomalyDetector

def test_chat_anomaly():
    detector = ChatAnomalyDetector(toxicity_threshold=0.5)
    
    # Test Normal
    event_normal = {
        "timestamp": 1000,
        "payload": {"author": "user1", "text": "hello"},
        "enrichments": {"toxicity": {"toxic": 0.1}}
    }
    res = detector.detect(event_normal)
    assert res["is_anomaly"] == "false"
    
    # Test Toxicity Spike
    event_toxic = {
        "timestamp": 1001,
        "payload": {"author": "user2", "text": "bad word"},
        "enrichments": {"toxicity": {"toxic": 0.9}}
    }
    res = detector.detect(event_toxic)
    assert res["is_anomaly"] == "true"
    assert res["type"] == "toxicity_spike"
    
    print("✅ Chat Anomaly Logic Verified")

def test_market_anomaly():
    detector = MarketAnomalyDetector(z_score_threshold=2.0)
    
    # Fill window
    for i in range(10):
        detector.detect(100.0)
    
    # Test Outlier
    res = detector.detect(150.0)
    assert res["is_anomaly"] == "true"
    assert "z_score" in res
    assert "mean" in res
    assert "std" in res
    
    # Test schema consistency
    expected_keys = {"is_anomaly", "type", "severity", "mean", "std", "z_score"}
    assert set(res.keys()).issuperset(expected_keys)
    
    print("✅ Market Anomaly Logic Verified")

if __name__ == "__main__":
    try:
        test_chat_anomaly()
        test_market_anomaly()
        print("\n🎉 All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
