"""ETL module for loading conferences data from the CFBD API to BigQuery."""

from typing import List, Dict, Any

from cfb_data.etl.base import NonSeasonalBaseETL
from cfb_data.config import TABLES


class ConferencesETL(NonSeasonalBaseETL):
    """ETL class for loading conferences data from the CFBD API to BigQuery."""
    
    def __init__(self, api_client=None, bq_client=None):
        """
        Initialize the conferences ETL process.
        
        Args:
            api_client: The CFBD API client to use. If None, a new client will be created.
            bq_client: The BigQuery client to use. If None, a new client will be created.
        """
        super().__init__(TABLES["conferences"], api_client, bq_client)
    
    def extract(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract conferences data.
        
        Args:
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of conferences data.
        """
        return self.api_client.get_conferences(**kwargs)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform conferences data.
        
        Args:
            data: The conferences data to transform.
            
        Returns:
            The transformed conferences data.
        """
        transformed_data = []
        
        for conference in data:
            # Extract the relevant fields
            transformed_conference = {
                "id": conference.get("id"),
                "name": conference.get("name"),
                "short_name": conference.get("short_name"),
                "abbreviation": conference.get("abbreviation"),
                "classification": conference.get("classification"),
            }
            
            transformed_data.append(transformed_conference)
            
        return transformed_data
