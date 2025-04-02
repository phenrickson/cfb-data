"""ETL module for loading drives data from the CFBD API to BigQuery."""

from typing import List, Dict, Any

from cfb_data.etl.base import SeasonalBaseETL
from cfb_data.config import TABLES


class DrivesETL(SeasonalBaseETL):
    """ETL class for loading drives data from the CFBD API to BigQuery."""
    
    def __init__(self, api_client=None, bq_client=None):
        """
        Initialize the drives ETL process.
        
        Args:
            api_client: The CFBD API client to use. If None, a new client will be created.
            bq_client: The BigQuery client to use. If None, a new client will be created.
        """
        super().__init__(TABLES["drives"], api_client, bq_client)
    
    def _extract_for_season(self, season: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract drives data for a specific season.
        
        Args:
            season: The season to extract data for.
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of drives data for the season.
        """
        return self.api_client.get_drives(year=season, **kwargs)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform drives data.
        
        Args:
            data: The drives data to transform.
            
        Returns:
            The transformed drives data.
        """
        transformed_data = []
        
        for drive in data:
            # Extract the relevant fields
            transformed_drive = {
                "game_id": drive.get("game_id"),
                "id": drive.get("id"),
                "drive_number": drive.get("drive_number"),
                "offense": drive.get("offense"),
                "offense_conference": drive.get("offense_conference"),
                "defense": drive.get("defense"),
                "defense_conference": drive.get("defense_conference"),
                "scoring": drive.get("scoring"),
                "start_period": drive.get("start_period"),
                "start_clock": drive.get("start_clock"),
                "start_yards_to_goal": drive.get("start_yards_to_goal"),
                "end_period": drive.get("end_period"),
                "end_clock": drive.get("end_clock"),
                "end_yards_to_goal": drive.get("end_yards_to_goal"),
                "plays": drive.get("plays"),
                "yards": drive.get("yards"),
                "drive_result": drive.get("drive_result"),
            }
            
            transformed_data.append(transformed_drive)
            
        return transformed_data
