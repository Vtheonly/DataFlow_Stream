import os
import pickle
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from utils.logger import get_logger

logger = get_logger(__name__)

class ToxicityClassifier:
    """
    Singleton class to load and use the Keras toxicity model.
    """
    _instance = None
    
    # Define paths relative to this file's location
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _MODEL_PATH = os.path.join(_BASE_DIR, "models/model.h5")
    _TOKENIZER_PATH = os.path.join(_BASE_DIR, "models/tokenizer.pickle")
    _MAX_SEQ_LENGTH = 200 # Must match the model's training configuration

    def __init__(self):
        if not os.path.exists(self._MODEL_PATH) or not os.path.exists(self._TOKENIZER_PATH):
            logger.error("Model or tokenizer file not found. NLP features will be disabled.")
            logger.error(f"Expected model at: {self._MODEL_PATH}")
            logger.error(f"Expected tokenizer at: {self._TOKENIZER_PATH}")
            self.model = None
            self.tokenizer = None
        else:
            try:
                self.model = load_model(self._MODEL_PATH)
                with open(self._TOKENIZER_PATH, 'rb') as handle:
                    self.tokenizer = pickle.load(handle)
                logger.info("Keras toxicity model and tokenizer loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load Keras model/tokenizer: {e}", exc_info=True)
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
        """
        if not self.model or not self.tokenizer:
            return {
                "toxic": 0.0, "severe_toxic": 0.0, "obscene": 0.0,
                "threat": 0.0, "insult": 0.0, "identity_hate": 0.0,
                "error": "Model not loaded"
            }
            
        try:
            # Preprocess the text
            sequence = self.tokenizer.texts_to_sequences([text])
            padded_sequence = pad_sequences(sequence, maxlen=self._MAX_SEQ_LENGTH)
            
            # Get prediction
            prediction = self.model.predict(padded_sequence, verbose=0)[0]
            
            # Format output
            labels = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
            scores = {label: float(score) for label, score in zip(labels, prediction)}
            return scores

        except Exception as e:
            logger.error(f"Error during toxicity prediction: {e}", exc_info=True)
            return {label: 0.0 for label in labels}
