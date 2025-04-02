"""ETL module for loading games data from the CFBD API to BigQuery."""

from typing import List, Dict, Any

from cfb_data.etl.base import SeasonalBaseETL
from cfb_data.config import TABLES


class GamesETL(SeasonalBaseETL):
    """ETL class for loading games data from the CFBD API to BigQuery."""
    
    def __init__(self, api_client=None, bq_client=None):
        """
        Initialize the games ETL process.
        
        Args:
            api_client: The CFBD API client to use. If None, a new client will be created.
            bq_client: The BigQuery client to use. If None, a new client will be created.
        """
        super().__init__(TABLES["games"], api_client, bq_client)
    
    def _extract_for_season(self, season: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract games data for a specific season.
        
        Args:
            season: The season to extract data for.
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of games data for the season.
        """
        return self.api_client.get_games(year=season, **kwargs)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform games data.
        
        Args:
            data: The games data to transform.
            
        Returns:
            The transformed games data.
        """
        transformed_data = []
        
        for game in data:
            # Extract the relevant fields
            transformed_game = {
                "id": game.get("id"),
                "season": game.get("season"),
                "week": game.get("week"),
                "season_type": game.get("season_type"),
                "start_date": game.get("start_date"),
                "neutral_site": game.get("neutral_site"),
                "conference_game": game.get("conference_game"),
                "attendance": game.get("attendance"),
                "venue_id": game.get("venue_id"),
                "venue": game.get("venue"),
                "home_team": game.get("home_team"),
                "home_conference": game.get("home_conference"),
                "home_points": game.get("home_points"),
                "away_team": game.get("away_team"),
                "away_conference": game.get("away_conference"),
                "away_points": game.get("away_points"),
            }
            
            transformed_data.append(transformed_game)
            
        return transformed_data
