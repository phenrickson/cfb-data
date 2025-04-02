"""ETL module for loading teams data from the CFBD API to BigQuery."""

from typing import List, Dict, Any

from cfb_data.etl.base import NonSeasonalBaseETL, SeasonalBaseETL
from cfb_data.config import TABLES


class TeamsETL(NonSeasonalBaseETL):
    """ETL class for loading teams data from the CFBD API to BigQuery."""
    
    def __init__(self, api_client=None, bq_client=None):
        """
        Initialize the teams ETL process.
        
        Args:
            api_client: The CFBD API client to use. If None, a new client will be created.
            bq_client: The BigQuery client to use. If None, a new client will be created.
        """
        super().__init__(TABLES["teams"], api_client, bq_client)
    
    def extract(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract teams data.
        
        Args:
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of teams data.
        """
        return self.api_client.get_teams(**kwargs)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform teams data.
        
        Args:
            data: The teams data to transform.
            
        Returns:
            The transformed teams data.
        """
        transformed_data = []
        
        for team in data:
            # Extract the relevant fields
            transformed_team = {
                "id": team.get("id"),
                "school": team.get("school"),
                "mascot": team.get("mascot"),
                "abbreviation": team.get("abbreviation"),
                "alt_name_1": team.get("alt_name_1"),
                "alt_name_2": team.get("alt_name_2"),
                "alt_name_3": team.get("alt_name_3"),
                "conference": team.get("conference"),
                "division": team.get("division"),
                "color": team.get("color"),
                "alt_color": team.get("alt_color"),
                "logos": team.get("logos"),
                "location": team.get("location"),
            }
            
            transformed_data.append(transformed_team)
            
        return transformed_data


class TeamsFbsETL(SeasonalBaseETL):
    """ETL class for loading FBS teams data from the CFBD API to BigQuery."""
    
    def __init__(self, api_client=None, bq_client=None):
        """
        Initialize the FBS teams ETL process.
        
        Args:
            api_client: The CFBD API client to use. If None, a new client will be created.
            bq_client: The BigQuery client to use. If None, a new client will be created.
        """
        super().__init__(TABLES["teams_fbs"], api_client, bq_client)
    
    def _extract_for_season(self, season: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract FBS teams data for a specific season.
        
        Args:
            season: The season to extract data for.
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of FBS teams data for the season.
        """
        return self.api_client.get_fbs_teams(year=season, **kwargs)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform FBS teams data.
        
        Args:
            data: The FBS teams data to transform.
            
        Returns:
            The transformed FBS teams data.
        """
        transformed_data = []
        
        for team in data:
            # Extract the relevant fields
            transformed_team = {
                "id": team.get("id"),
                "school": team.get("school"),
                "mascot": team.get("mascot"),
                "abbreviation": team.get("abbreviation"),
                "alt_name_1": team.get("alt_name_1"),
                "alt_name_2": team.get("alt_name_2"),
                "alt_name_3": team.get("alt_name_3"),
                "conference": team.get("conference"),
                "division": team.get("division"),
                "color": team.get("color"),
                "alt_color": team.get("alt_color"),
                "logos": team.get("logos"),
                "location": team.get("location"),
            }
            
            transformed_data.append(transformed_team)
            
        return transformed_data


class TeamTalentETL(SeasonalBaseETL):
    """ETL class for loading team talent data from the CFBD API to BigQuery."""
    
    def __init__(self, api_client=None, bq_client=None):
        """
        Initialize the team talent ETL process.
        
        Args:
            api_client: The CFBD API client to use. If None, a new client will be created.
            bq_client: The BigQuery client to use. If None, a new client will be created.
        """
        super().__init__(TABLES["talent"], api_client, bq_client)
    
    def _extract_for_season(self, season: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract team talent data for a specific season.
        
        Args:
            season: The season to extract data for.
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of team talent data for the season.
        """
        return self.api_client.get_team_talent(year=season, **kwargs)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform team talent data.
        
        Args:
            data: The team talent data to transform.
            
        Returns:
            The transformed team talent data.
        """
        transformed_data = []
        
        for talent in data:
            # Extract the relevant fields
            transformed_talent = {
                "year": talent.get("year"),
                "school": talent.get("school"),
                "talent": talent.get("talent"),
            }
            
            transformed_data.append(transformed_talent)
            
        return transformed_data
