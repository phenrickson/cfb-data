"""ETL module for loading plays data from the CFBD API to BigQuery."""

from typing import List, Dict, Any

from cfb_data.etl.base import SeasonalBaseETL, NonSeasonalBaseETL
from cfb_data.config import TABLES


class PlaysETL(SeasonalBaseETL):
    """ETL class for loading plays data from the CFBD API to BigQuery."""
    
    def __init__(self, api_client=None, bq_client=None):
        """
        Initialize the plays ETL process.
        
        Args:
            api_client: The CFBD API client to use. If None, a new client will be created.
            bq_client: The BigQuery client to use. If None, a new client will be created.
        """
        super().__init__(TABLES["plays"], api_client, bq_client)
    
    def _extract_for_season(self, season: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract plays data for a specific season.
        
        Args:
            season: The season to extract data for.
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of plays data for the season.
        """
        return self.api_client.get_plays(year=season, **kwargs)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform plays data.
        
        Args:
            data: The plays data to transform.
            
        Returns:
            The transformed plays data.
        """
        transformed_data = []
        
        for play in data:
            # Extract the relevant fields
            transformed_play = {
                "game_id": play.get("game_id"),
                "id": play.get("id"),
                "drive_id": play.get("drive_id"),
                "drive_number": play.get("drive_number"),
                "period": play.get("period"),
                "clock": play.get("clock"),
                "offense_team": play.get("offense"),
                "offense_conference": play.get("offense_conference"),
                "defense_team": play.get("defense"),
                "defense_conference": play.get("defense_conference"),
                "yard_line": play.get("yard_line"),
                "yards_to_goal": play.get("yards_to_goal"),
                "down": play.get("down"),
                "distance": play.get("distance"),
                "play_type": play.get("play_type"),
                "play_text": play.get("play_text"),
                "yards_gained": play.get("yards_gained"),
            }
            
            transformed_data.append(transformed_play)
            
        return transformed_data


class PlayTypesETL(NonSeasonalBaseETL):
    """ETL class for loading play types data from the CFBD API to BigQuery."""
    
    def __init__(self, api_client=None, bq_client=None):
        """
        Initialize the play types ETL process.
        
        Args:
            api_client: The CFBD API client to use. If None, a new client will be created.
            bq_client: The BigQuery client to use. If None, a new client will be created.
        """
        super().__init__(TABLES["play_types"], api_client, bq_client)
    
    def extract(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract play types data.
        
        Args:
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of play types data.
        """
        return self.api_client.get_play_types(**kwargs)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform play types data.
        
        Args:
            data: The play types data to transform.
            
        Returns:
            The transformed play types data.
        """
        transformed_data = []
        
        for play_type in data:
            # Extract the relevant fields
            transformed_play_type = {
                "id": play_type.get("id"),
                "text": play_type.get("text"),
                "abbreviation": play_type.get("abbreviation"),
            }
            
            transformed_data.append(transformed_play_type)
            
        return transformed_data
