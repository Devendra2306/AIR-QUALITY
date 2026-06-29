import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import io
from app.core.database import db_manager
from app.config.settings import settings
from app.config.logging_config import logger


class ExportService:
    """Service for exporting data in multiple formats."""
    
    def __init__(self):
        self.export_dir = Path(settings.EXPORT_TEMP_DIR)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.max_rows = settings.EXPORT_MAX_ROWS
    
    def _execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """Execute query and return DataFrame."""
        try:
            with db_manager.get_connection() as conn:
                if params:
                    result = conn.execute(query, params)
                else:
                    result = conn.execute(query)
                return result.df()
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def export_to_csv(
        self,
        query: str,
        filename: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export query results to CSV."""
        df = self._execute_query(query, params)
        
        if len(df) > self.max_rows:
            logger.warning(f"Limiting export to {self.max_rows} rows")
            df = df.head(self.max_rows)
        
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.export_dir / filename
        df.to_csv(filepath, index=False)
        
        logger.info(f"Exported {len(df)} rows to CSV: {filepath}")
        return str(filepath)
    
    def export_to_json(
        self,
        query: str,
        filename: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export query results to JSON."""
        df = self._execute_query(query, params)
        
        if len(df) > self.max_rows:
            logger.warning(f"Limiting export to {self.max_rows} rows")
            df = df.head(self.max_rows)
        
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.export_dir / filename
        df.to_json(filepath, orient="records", indent=2)
        
        logger.info(f"Exported {len(df)} rows to JSON: {filepath}")
        return str(filepath)
    
    def export_to_excel(
        self,
        query: str,
        filename: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        sheet_name: str = "Data"
    ) -> str:
        """Export query results to Excel."""
        df = self._execute_query(query, params)
        
        if len(df) > self.max_rows:
            logger.warning(f"Limiting export to {self.max_rows} rows")
            df = df.head(self.max_rows)
        
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        filepath = self.export_dir / filename
        df.to_excel(filepath, sheet_name=sheet_name, index=False, engine='openpyxl')
        
        logger.info(f"Exported {len(df)} rows to Excel: {filepath}")
        return str(filepath)
    
    def export_to_parquet(
        self,
        query: str,
        filename: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export query results to Parquet."""
        df = self._execute_query(query, params)
        
        if len(df) > self.max_rows:
            logger.warning(f"Limiting export to {self.max_rows} rows")
            df = df.head(self.max_rows)
        
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
        
        filepath = self.export_dir / filename
        df.to_parquet(filepath, engine='pyarrow')
        
        logger.info(f"Exported {len(df)} rows to Parquet: {filepath}")
        return str(filepath)
    
    def get_export_data(
        self,
        format: str,
        location_id: Optional[int] = None,
        parameter: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> bytes:
        """Get export data as bytes for download."""
        # Build query
        base_query = """
        SELECT 
            location_id,
            location,
            latitude,
            longitude,
            parameter,
            unit,
            value,
            measurement_time,
            quality_score
        FROM raw.measurements
        WHERE quality_score > 0.5
        """
        
        conditions = []
        params = {}
        
        if location_id:
            conditions.append("location_id = $location_id")
            params["location_id"] = location_id
        
        if parameter:
            conditions.append("parameter = $parameter")
            params["parameter"] = parameter
        
        if date_from:
            conditions.append("measurement_time >= $date_from")
            params["date_from"] = date_from
        
        if date_to:
            conditions.append("measurement_time <= $date_to")
            params["date_to"] = date_to
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        base_query += " ORDER BY measurement_time DESC"
        
        df = self._execute_query(base_query, params)
        
        if len(df) > self.max_rows:
            df = df.head(self.max_rows)
        
        # Convert to requested format
        if format == "csv":
            output = io.StringIO()
            df.to_csv(output, index=False)
            return output.getvalue().encode('utf-8')
        elif format == "json":
            return df.to_json(orient="records").encode('utf-8')
        elif format == "excel":
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            return output.getvalue()
        elif format == "parquet":
            output = io.BytesIO()
            df.to_parquet(output, engine='pyarrow')
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_available_exports(self) -> List[Dict[str, Any]]:
        """Get list of available export files."""
        exports = []
        
        for filepath in self.export_dir.glob("*"):
            if filepath.is_file():
                exports.append({
                    "filename": filepath.name,
                    "size": filepath.stat().st_size,
                    "created": datetime.fromtimestamp(filepath.stat().st_ctime),
                    "format": filepath.suffix[1:]
                })
        
        return sorted(exports, key=lambda x: x["created"], reverse=True)
    
    def delete_export(self, filename: str) -> bool:
        """Delete an export file."""
        filepath = self.export_dir / filename
        
        if filepath.exists():
            filepath.unlink()
            logger.info(f"Deleted export: {filename}")
            return True
        
        return False
