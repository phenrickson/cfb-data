"""Generic ETL module for loading data from the CFBD API to BigQuery."""

from typing import List, Dict, Any, Optional, Callable, Union
import time

from loguru import logger
from tqdm import tqdm

from cfb_data.api_client import CFBDApiClient
from cfb_data.bigquery_client import BigQueryClient
from cfb_data.config import FIRST_SEASON, LAST_SEASON, TABLES


class GenericETL:
    """Generic ETL class for loading data from the CFBD API to BigQuery."""
    
    def __init__(
        self,
        table_name: str,
        api_method: Union[str, Callable],
        is_seasonal: bool = False,
        transform_func: Optional[Callable] = None,
        api_client: Optional[CFBDApiClient] = None,
        bq_client: Optional[BigQueryClient] = None,
    ):
        """
        Initialize the generic ETL process.
        
        Args:
            table_name: The name of the table to load data into.
            api_method: The API method to call, either as a string (method name on api_client)
                        or a callable function.
            is_seasonal: Whether the data is seasonal (requires a year parameter).
            transform_func: Optional function to transform the data before loading.
            api_client: The CFBD API client to use. If None, a new client will be created.
            bq_client: The BigQuery client to use. If None, a new client will be created.
        """
        self.table_name = table_name
        self.api_method = api_method
        self.is_seasonal = is_seasonal
        self.transform_func = transform_func
        self.api_client = api_client or CFBDApiClient()
        self.bq_client = bq_client or BigQueryClient()
        
    def _get_api_method(self) -> Callable:
        """
        Get the API method to call.
        
        Returns:
            The API method as a callable.
        """
        if callable(self.api_method):
            return self.api_method
        
        # If api_method is a string, get the corresponding method from the API client
        if hasattr(self.api_client, self.api_method):
            return getattr(self.api_client, self.api_method)
        
        raise ValueError(f"API method {self.api_method} not found on API client")
        
    def extract(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract data from the CFBD API.
        
        Args:
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of data items.
        """
        api_method = self._get_api_method()
        
        if self.is_seasonal:
            year = kwargs.pop("year", None)
            
            if year is not None:
                logger.info(f"Extracting {self.table_name} data for season {year}")
                return api_method(year=year, **kwargs)
            
            # If no year is specified, extract data for all years
            all_data = []
            for season in tqdm(range(FIRST_SEASON, LAST_SEASON + 1), 
                              desc=f"Extracting {self.table_name} by season"):
                logger.info(f"Extracting {self.table_name} data for season {season}")
                season_data = api_method(year=season, **kwargs)
                all_data.extend(season_data)
                
                # Add a small delay between seasons to avoid rate limiting
                time.sleep(1)
                
            return all_data
        else:
            # Non-seasonal data
            logger.info(f"Extracting {self.table_name} data")
            return api_method(**kwargs)
        
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform the data before loading it into BigQuery.
        
        Args:
            data: The data to transform.
            
        Returns:
            The transformed data.
        """
        if self.transform_func:
            return self.transform_func(data)
        
        # Default implementation returns the data unchanged
        return data
        
    def load(self, data: List[Dict[str, Any]], write_disposition: str = "WRITE_APPEND") -> None:
        """
        Load the data into BigQuery.
        
        Args:
            data: The data to load.
            write_disposition: The write disposition for the load job.
        """
        if not data:
            logger.warning(f"No data to load into {self.table_name}")
            return
            
        logger.info(f"Loading {len(data)} records into {self.table_name}")
        self.bq_client.load_data_from_json(self.table_name, data, write_disposition)
        
    def run(self, **kwargs) -> None:
        """
        Run the ETL process.
        
        Args:
            **kwargs: Additional parameters for the extract method.
        """
        logger.info(f"Running ETL process for {self.table_name}")
        
        data = self.extract(**kwargs)
        transformed_data = self.transform(data)
        
        load_options = kwargs.pop("load_options", {})
        write_disposition = load_options.get("write_disposition", "WRITE_APPEND")
        self.load(transformed_data, write_disposition)
        
        logger.success(f"ETL process for {self.table_name} completed")
        
    def run_historical(self, start_season: int = FIRST_SEASON, 
                       end_season: int = LAST_SEASON, **kwargs) -> None:
        """
        Run the ETL process for historical data across multiple seasons.
        
        Args:
            start_season: The first season to load data for.
            end_season: The last season to load data for.
            **kwargs: Additional parameters for the extract method.
        """
        if not self.is_seasonal:
            logger.info(f"Running historical ETL process for {self.table_name}")
            return self.run(**kwargs)
            
        logger.info(
            f"Running historical ETL process for {self.table_name} "
            f"from {start_season} to {end_season}"
        )
        
        all_data = []
        
        # Process each season
        for season in tqdm(range(start_season, end_season + 1), 
                          desc=f"Loading {self.table_name} by season"):
            logger.info(f"Processing season {season}")
            
            # Extract data for this season
            season_kwargs = {**kwargs, "year": season}
            data = self.extract(**season_kwargs)
            
            if data:
                transformed_data = self.transform(data)
                all_data.extend(transformed_data)
                
            # Add a small delay between seasons to avoid rate limiting
            time.sleep(1)
            
        # Load all data at once
        if all_data:
            write_disposition = kwargs.get("write_disposition", "WRITE_TRUNCATE")
            self.load(all_data, write_disposition)
            
        logger.success(
            f"Historical ETL process for {self.table_name} completed "
            f"with {len(all_data)} total records"
        )


# Define transformation functions for specific tables if needed

def transform_games(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

def transform_teams(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

def transform_talent(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

def transform_plays(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

def transform_play_types(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

def transform_drives(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

def transform_conferences(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

def transform_venues(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

def transform_coaches(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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


# Create ETL instances for each table
def create_etl_instances(api_client=None, bq_client=None):
    """
    Create ETL instances for all tables.
    
    Args:
        api_client: The CFBD API client to use. If None, a new client will be created.
        bq_client: The BigQuery client to use. If None, a new client will be created.
        
    Returns:
        Dict mapping table names to ETL instances.
    """
    return {
        TABLES["games"]: GenericETL(
            TABLES["games"],
            "get_games",
            is_seasonal=True,
            transform_func=transform_games,
            api_client=api_client,
            bq_client=bq_client,
        ),
        TABLES["teams"]: GenericETL(
            TABLES["teams"],
            "get_teams",
            is_seasonal=False,
            transform_func=transform_teams,
            api_client=api_client,
            bq_client=bq_client,
        ),
        TABLES["teams_fbs"]: GenericETL(
            TABLES["teams_fbs"],
            "get_fbs_teams",
            is_seasonal=True,
            transform_func=transform_teams,
            api_client=api_client,
            bq_client=bq_client,
        ),
        TABLES["talent"]: GenericETL(
            TABLES["talent"],
            "get_team_talent",
            is_seasonal=True,
            transform_func=transform_talent,
            api_client=api_client,
            bq_client=bq_client,
        ),
        TABLES["plays"]: GenericETL(
            TABLES["plays"],
            "get_plays",
            is_seasonal=True,
            transform_func=transform_plays,
            api_client=api_client,
            bq_client=bq_client,
        ),
        TABLES["play_types"]: GenericETL(
            TABLES["play_types"],
            "get_play_types",
            is_seasonal=False,
            transform_func=transform_play_types,
            api_client=api_client,
            bq_client=bq_client,
        ),
        TABLES["drives"]: GenericETL(
            TABLES["drives"],
            "get_drives",
            is_seasonal=True,
            transform_func=transform_drives,
            api_client=api_client,
            bq_client=bq_client,
        ),
        TABLES["conferences"]: GenericETL(
            TABLES["conferences"],
            "get_conferences",
            is_seasonal=False,
            transform_func=transform_conferences,
            api_client=api_client,
            bq_client=bq_client,
        ),
        TABLES["venues"]: GenericETL(
            TABLES["venues"],
            "get_venues",
            is_seasonal=False,
            transform_func=transform_venues,
            api_client=api_client,
            bq_client=bq_client,
        ),
        TABLES["coaches"]: GenericETL(
            TABLES["coaches"],
            "get_coaches",
            is_seasonal=False,
            transform_func=transform_coaches,
            api_client=api_client,
            bq_client=bq_client,
        ),
    }
