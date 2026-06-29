import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.pipeline.extractors.base_extractor import BaseExtractor
from app.config.settings import settings
from app.config.logging_config import logger


class OpenAQExtractor(BaseExtractor):
    """Extractor for OpenAQ API with rate limiting."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(max_retries=3, backoff_factor=2.0)
        self.api_key = api_key or settings.OPENAQ_API_KEY
        self.base_url = settings.OPENAQ_API_BASE_URL
        self.timeout = settings.OPENAQ_TIMEOUT
        self.rate_limit = settings.OPENAQ_RATE_LIMIT
        self._last_request_time = 0
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make API request with rate limiting."""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < (1.0 / self.rate_limit):
            sleep_time = (1.0 / self.rate_limit) - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
        
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        url = f"{self.base_url}{endpoint}"
        
        def _request():
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
        
        return self._retry_with_backoff(_request)
    
    def extract_locations(
        self,
        limit: int = 1000,
        country: Optional[str] = None,
        city: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract location data."""
        params = {"limit": limit}
        if country:
            params["country"] = country
        if city:
            params["city"] = city
        
        data = self._make_request("/locations", params)
        results = data.get("results", [])
        logger.info(f"Extracted {len(results)} locations")
        return results
    
    def extract_latest_measurements(
        self,
        location_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Extract latest measurements for a location."""
        params = {"limit": limit}
        data = self._make_request(f"/locations/{location_id}/latest", params)
        results = data.get("results", [])
        logger.info(f"Extracted {len(results)} measurements for location {location_id}")
        return results
    
    def extract_measurements_by_date(
        self,
        location_id: int,
        date_from: str,
        date_to: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Extract measurements for a date range."""
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "limit": limit
        }
        data = self._make_request(f"/locations/{location_id}/measurements", params)
        results = data.get("results", [])
        logger.info(f"Extracted {len(results)} measurements for location {location_id} from {date_from} to {date_to}")
        return results
    
    def extract(self, **kwargs) -> List[Dict[str, Any]]:
        """Extract data based on parameters."""
        extract_type = kwargs.get("type", "locations")
        
        if extract_type == "locations":
            return self.extract_locations(
                limit=kwargs.get("limit", 1000),
                country=kwargs.get("country"),
                city=kwargs.get("city")
            )
        elif extract_type == "latest":
            return self.extract_latest_measurements(
                location_id=kwargs["location_id"],
                limit=kwargs.get("limit", 100)
            )
        elif extract_type == "measurements":
            return self.extract_measurements_by_date(
                location_id=kwargs["location_id"],
                date_from=kwargs["date_from"],
                date_to=kwargs["date_to"],
                limit=kwargs.get("limit", 1000)
            )
        else:
            raise ValueError(f"Unknown extract type: {extract_type}")
    
    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate extracted data."""
        if not data:
            logger.warning("No data to validate")
            return False
        
        required_fields = ["id"]
        for item in data:
            if not all(field in item for field in required_fields):
                logger.warning(f"Missing required fields in data: {item}")
                return False
        
        logger.info(f"Validated {len(data)} records")
        return True
