from typing import List, Dict, Any, Optional
from app.core.database import db_manager
from app.pipeline.extractors.openaq_extractor import OpenAQExtractor
from app.config.logging_config import logger


class LocationService:
    """Service for managing sensor locations."""
    
    def __init__(self):
        self.extractor = OpenAQExtractor()
    
    def get_all_locations(
        self,
        active_only: bool = True,
        country: Optional[str] = None,
        city: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all locations from database."""
        query = """
        SELECT 
            location_id,
            name,
            city,
            country,
            latitude,
            longitude,
            timezone,
            is_active,
            last_updated
        FROM staging.locations
        WHERE 1=1
        """
        
        params = {}
        
        if active_only:
            query += " AND is_active = TRUE"
        
        if country:
            query += " AND country = $country"
            params["country"] = country
        
        if city:
            query += " AND city = $city"
            params["city"] = city
        
        query += " ORDER BY country, city, name"
        
        try:
            with db_manager.get_connection() as conn:
                if params:
                    result = conn.execute(query, params)
                else:
                    result = conn.execute(query)
                return result.df().to_dict("records")
        except Exception as e:
            logger.error(f"Error fetching locations: {str(e)}")
            return []
    
    def get_location_by_id(self, location_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific location by ID."""
        query = """
        SELECT 
            location_id,
            name,
            city,
            country,
            latitude,
            longitude,
            timezone,
            is_active,
            last_updated
        FROM staging.locations
        WHERE location_id = $location_id
        """
        
        try:
            with db_manager.get_connection() as conn:
                result = conn.execute(query, {"location_id": location_id})
                df = result.df()
                if df.empty:
                    return None
                return df.iloc[0].to_dict()
        except Exception as e:
            logger.error(f"Error fetching location {location_id}: {str(e)}")
            return None
    
    def add_location(self, location_data: Dict[str, Any]) -> bool:
        """Add a new location."""
        query = """
        INSERT INTO staging.locations (
            location_id, name, city, country, latitude, longitude, timezone, is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with db_manager.get_connection() as conn:
                conn.execute(query, [
                    location_data.get("location_id"),
                    location_data.get("name"),
                    location_data.get("city"),
                    location_data.get("country"),
                    location_data.get("latitude"),
                    location_data.get("longitude"),
                    location_data.get("timezone"),
                    location_data.get("is_active", True)
                ])
            logger.info(f"Added location {location_data.get('location_id')}")
            return True
        except Exception as e:
            logger.error(f"Error adding location: {str(e)}")
            return False
    
    def update_location(self, location_id: int, location_data: Dict[str, Any]) -> bool:
        """Update an existing location."""
        updates = []
        params = {"location_id": location_id}
        
        for key, value in location_data.items():
            if key != "location_id":
                updates.append(f"{key} = ${key}")
                params[key] = value
        
        if not updates:
            return False
        
        query = f"""
        UPDATE staging.locations
        SET {', '.join(updates)}, last_updated = CURRENT_TIMESTAMP
        WHERE location_id = $location_id
        """
        
        try:
            with db_manager.get_connection() as conn:
                conn.execute(query, params)
            logger.info(f"Updated location {location_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating location {location_id}: {str(e)}")
            return False
    
    def deactivate_location(self, location_id: int) -> bool:
        """Deactivate a location."""
        return self.update_location(location_id, {"is_active": False})
    
    def activate_location(self, location_id: int) -> bool:
        """Activate a location."""
        return self.update_location(location_id, {"is_active": True})
    
    def sync_locations_from_api(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        limit: int = 1000
    ) -> Dict[str, int]:
        """Sync locations from OpenAQ API."""
        try:
            # Fetch locations from API
            api_locations = self.extractor.extract(
                type="locations",
                country=country,
                city=city,
                limit=limit
            )
            
            added = 0
            updated = 0
            errors = 0
            
            for loc in api_locations:
                location_data = {
                    "location_id": loc.get("id"),
                    "name": loc.get("name"),
                    "city": loc.get("city"),
                    "country": loc.get("country"),
                    "latitude": loc.get("coordinates", {}).get("latitude") if isinstance(loc.get("coordinates"), dict) else None,
                    "longitude": loc.get("coordinates", {}).get("longitude") if isinstance(loc.get("coordinates"), dict) else None,
                    "timezone": loc.get("timezone"),
                    "is_active": True
                }
                
                # Check if location exists
                existing = self.get_location_by_id(location_data["location_id"])
                
                if existing:
                    # Update existing
                    if self.update_location(location_data["location_id"], location_data):
                        updated += 1
                    else:
                        errors += 1
                else:
                    # Add new
                    if self.add_location(location_data):
                        added += 1
                    else:
                        errors += 1
            
            logger.info(f"Location sync: {added} added, {updated} updated, {errors} errors")
            return {"added": added, "updated": updated, "errors": errors}
            
        except Exception as e:
            logger.error(f"Error syncing locations from API: {str(e)}")
            return {"added": 0, "updated": 0, "errors": 1}
    
    def get_location_statistics(self, location_id: int) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific location."""
        query = """
        SELECT 
            l.location_id,
            l.name,
            l.city,
            l.country,
            COUNT(DISTINCT m.parameter) as parameter_count,
            COUNT(m.id) as total_measurements,
            MAX(m.measurement_time) as last_measurement_time,
            AVG(m.quality_score) as avg_quality_score,
            MIN(m.measurement_time) as first_measurement_time
        FROM staging.locations l
        LEFT JOIN raw.measurements m ON l.location_id = m.location_id
        WHERE l.location_id = $location_id
        GROUP BY l.location_id, l.name, l.city, l.country
        """
        
        try:
            with db_manager.get_connection() as conn:
                result = conn.execute(query, {"location_id": location_id})
                df = result.df()
                if df.empty:
                    return None
                return df.iloc[0].to_dict()
        except Exception as e:
            logger.error(f"Error fetching location statistics: {str(e)}")
            return None
    
    def search_locations(self, search_term: str) -> List[Dict[str, Any]]:
        """Search locations by name, city, or country."""
        query = """
        SELECT 
            location_id,
            name,
            city,
            country,
            latitude,
            longitude,
            is_active
        FROM staging.locations
        WHERE 
            LOWER(name) LIKE $search_term OR
            LOWER(city) LIKE $search_term OR
            LOWER(country) LIKE $search_term
        ORDER BY country, city, name
        LIMIT 50
        """
        
        try:
            with db_manager.get_connection() as conn:
                result = conn.execute(query, {"search_term": f"%{search_term.lower()}%"})
                return result.df().to_dict("records")
        except Exception as e:
            logger.error(f"Error searching locations: {str(e)}")
            return []
    
    def get_location_groups(self) -> List[Dict[str, Any]]:
        """Get locations grouped by country and city."""
        query = """
        SELECT 
            country,
            city,
            COUNT(*) as location_count,
            COUNT(DISTINCT parameter) as parameter_count
        FROM presentation.location_summary
        WHERE is_active = TRUE
        GROUP BY country, city
        ORDER BY country, city
        """
        
        try:
            with db_manager.get_connection() as conn:
                result = conn.execute(query)
                return result.df().to_dict("records")
        except Exception as e:
            logger.error(f"Error fetching location groups: {str(e)}")
            return []
