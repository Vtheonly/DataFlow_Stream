import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from utils.logger import get_logger

logger = get_logger(__name__)

class ToxicityClassifier:
    """
    Singleton class using Hugging Face Transformers.
    Automatically downloads 'unitary/toxic-bert' on first run.
    """
    _instance = None
    MODEL_NAME = "unitary/toxic-bert"

    def __init__(self):
        try:
            logger.info(f"Loading Hugging Face model: {self.MODEL_NAME}...")
            # This will download the model (~260MB) if not present
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME)
            logger.info("Toxicity model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load NLP model: {e}", exc_info=True)
            self.model = None
            self.tokenizer = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ToxicityClassifier()
        return cls._instance

    def predict(self, text: str) -> dict:
        """
        Predicts toxicity scores for a given text.
        Returns a dictionary mapping labels to float scores (0.0 to 1.0).
        """
        labels = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
        default_result = {label: 0.0 for label in labels}

        if not self.model or not self.tokenizer:
            return default_result
            
        try:
            # Tokenize input
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            # Run inference (no gradient calculation needed for inference)
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Apply sigmoid to convert logits to probabilities (0 to 1)
            probs = torch.sigmoid(outputs.logits).squeeze().tolist()
            
            # Handle edge case where single output is float, not list
            if isinstance(probs, float):
                probs = [probs]
                
            # Create the result dictionary
            return {label: float(score) for label, score in zip(labels, probs)}

        except Exception as e:
            logger.error(f"Error during toxicity prediction: {e}")
            return default_result