from abc import ABC, abstractmethod

class BaseStreamSource(ABC):
    """
    Abstract Base Class for all data stream sources.
    Defines the contract that all adapters must follow.
    """
    
    @abstractmethod
    async def connect(self):
        """Connect to the data source."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_event(self):
        """Fetch a single event from the data source."""
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_event: dict) -> dict:
        """Normalize the raw event into a unified schema."""
        raise NotImplementedError
    
    @abstractmethod
    async def run(self):
        """The main loop to run the stream."""
        raise NotImplementedError