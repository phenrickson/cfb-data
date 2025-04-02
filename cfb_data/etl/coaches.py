"""ETL module for loading coaches data from the CFBD API to BigQuery."""

from typing import List, Dict, Any

from cfb_data.etl.base import NonSeasonalBaseETL
from cfb_data.config import TABLES


class CoachesETL(NonSeasonalBaseETL):
    """ETL class for loading coaches data from the CFBD API to BigQuery."""
    
    def __init__(self, api_client=None, bq_client=None):
        """
        Initialize the coaches ETL process.
        
        Args:
            api_client: The CFBD API client to use. If None, a new client will be created.
            bq_client: The BigQuery client to use. If None, a new client will be created.
        """
        super().__init__(TABLES["coaches"], api_client, bq_client)
    
    def extract(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract coaches data.
        
        Args:
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of coaches data.
        """
        return self.api_client.get_coaches(**kwargs)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform coaches data.
        
        Args:
            data: The coaches data to transform.
            
        Returns:
            The transformed coaches data.
        """
        transformed_data = []
        
        for coach in data:
            # Extract the relevant fields
            transformed_coach = {
                "id": coach.get("id"),
                "first_name": coach.get("first_name"),
                "last_name": coach.get("last_name"),
                "seasons": coach.get("seasons"),
            }
            
            transformed_data.append(transformed_coach)
            
        return transformed_data
