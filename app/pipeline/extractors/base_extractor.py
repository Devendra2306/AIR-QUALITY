from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time
from app.config.logging_config import logger


class BaseExtractor(ABC):
    """Base class for data extractors with retry logic."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    def _retry_with_backoff(self, func, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed: {str(e)}")
        
        raise last_exception
    
    @abstractmethod
    def extract(self, **kwargs) -> List[Dict[str, Any]]:
        """Extract data from source."""
        pass
    
    @abstractmethod
    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate extracted data."""
        pass
