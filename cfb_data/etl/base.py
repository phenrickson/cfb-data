"""Base ETL module for loading data from the CFBD API to BigQuery."""

from typing import List, Dict, Any, Optional, Callable, Union
import time

from loguru import logger
from tqdm import tqdm

from cfb_data.api_client import CFBDApiClient
from cfb_data.bigquery_client import BigQueryClient
from cfb_data.config import FIRST_SEASON, LAST_SEASON


class BaseETL:
    """Base ETL class for loading data from the CFBD API to BigQuery."""
    
    def __init__(
        self,
        table_name: str,
        api_client: Optional[CFBDApiClient] = None,
        bq_client: Optional[BigQueryClient] = None,
    ):
        """
        Initialize the base ETL process.
        
        Args:
            table_name: The name of the table to load data into.
            api_client: The CFBD API client to use. If None, a new client will be created.
            bq_client: The BigQuery client to use. If None, a new client will be created.
        """
        self.table_name = table_name
        self.api_client = api_client or CFBDApiClient()
        self.bq_client = bq_client or BigQueryClient()
        
    def extract(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract data from the CFBD API.
        
        Args:
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of data items.
        """
        raise NotImplementedError("Subclasses must implement extract method")
        
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform the data before loading it into BigQuery.
        
        Args:
            data: The data to transform.
            
        Returns:
            The transformed data.
        """
        raise NotImplementedError("Subclasses must implement transform method")
        
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
        raise NotImplementedError("Subclasses must implement run_historical method")


class SeasonalBaseETL(BaseETL):
    """Base ETL class for seasonal data (requires a year parameter)."""
    
    def extract(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract data from the CFBD API for a specific season.
        
        Args:
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of data items.
        """
        year = kwargs.pop("year", None)
        
        if year is not None:
            logger.info(f"Extracting {self.table_name} data for season {year}")
            return self._extract_for_season(year, **kwargs)
        
        # If no year is specified, extract data for all years
        all_data = []
        for season in tqdm(range(FIRST_SEASON, LAST_SEASON + 1), 
                          desc=f"Extracting {self.table_name} by season"):
            logger.info(f"Extracting {self.table_name} data for season {season}")
            season_data = self._extract_for_season(season, **kwargs)
            all_data.extend(season_data)
            
            # Add a small delay between seasons to avoid rate limiting
            time.sleep(1)
            
        return all_data
    
    def _extract_for_season(self, season: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract data for a specific season.
        
        Args:
            season: The season to extract data for.
            **kwargs: Additional parameters for the API call.
            
        Returns:
            List of data items for the season.
        """
        raise NotImplementedError("Subclasses must implement _extract_for_season method")
    
    def run_historical(self, start_season: int = FIRST_SEASON, 
                       end_season: int = LAST_SEASON, **kwargs) -> None:
        """
        Run the ETL process for historical data across multiple seasons.
        
        Args:
            start_season: The first season to load data for.
            end_season: The last season to load data for.
            **kwargs: Additional parameters for the extract method.
        """
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
            data = self._extract_for_season(season, **kwargs)
            
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


class NonSeasonalBaseETL(BaseETL):
    """Base ETL class for non-seasonal data."""
    
    def run_historical(self, **kwargs) -> None:
        """
        Run the ETL process for historical data.
        For non-seasonal data, this is the same as run().
        
        Args:
            **kwargs: Additional parameters for the extract method.
        """
        logger.info(f"Running historical ETL process for {self.table_name}")
        return self.run(**kwargs)
