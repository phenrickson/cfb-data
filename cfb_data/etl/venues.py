"""ETL module for loading venues data from the CFBD API to BigQuery."""

from typing import List, Dict, Any

from cfb_data.etl.base import NonSeasonalBaseETL
from cfb_data.config import TABLES


class VenuesETL(NonSeasonalBaseETL):
    """ETL class for loading venues data from the CFBD API to BigQuery."""
    
    def __init__(self, api_client=None, bq_client=None):
        """
        Initialize the venues ETL process.
        
        Args:
            api_client: The CFBD API client to use. If None, a new client will be created.
            bq_client: The BigQuery client to use. If None, a new client will be created.
        """
        super().__init__(TABLES["venues"], api_client, bq_client)
    
    def extract(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract venues data.
        
        Args:
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of venues data.
        """
        return self.api_client.get_venues(**kwargs)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform venues data.
        
        Args:
            data: The venues data to transform.
            
        Returns:
            The transformed venues data.
        """
        transformed_data = []
        
        for venue in data:
            # Extract the relevant fields
            transformed_venue = {
                "id": venue.get("id"),
                "name": venue.get("name"),
                "city": venue.get("city"),
                "state": venue.get("state"),
                "zip": venue.get("zip"),
                "country_code": venue.get("country_code"),
                "timezone": venue.get("timezone"),
                "latitude": venue.get("latitude"),
                "longitude": venue.get("longitude"),
                "elevation": venue.get("elevation"),
                "capacity": venue.get("capacity"),
                "year_constructed": venue.get("year_constructed"),
                "grass": venue.get("grass"),
                "dome": venue.get("dome"),
            }
            
            transformed_data.append(transformed_venue)
            
        return transformed_data
