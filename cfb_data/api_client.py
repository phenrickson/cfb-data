import json
import time
from datetime import datetime
from pathlib import Path
import hashlib
import os

import cfbd
from loguru import logger

from cfb_data.config import (
    CFBD_API_KEY,
    MIN_API_CALL_INTERVAL,
    API_CACHE_DIR,
    API_CALL_LOG,
)


class APIRateLimitError(Exception):
    """Exception raised when API rate limit is exceeded."""
    pass


class CFBDApiClient:
    """Client for the College Football Data API with rate limiting and caching."""

    def __init__(self, use_cache=True):
        """
        Initialize the CFBD API client.
        
        Args:
            use_cache (bool): Whether to use caching for API responses.
        """
        self.use_cache = use_cache
        self.last_call_time = 0
        self._init_api_client()
        self._init_call_tracking()

    def _init_api_client(self):
        """Initialize the CFBD API client configuration."""
        if not CFBD_API_KEY:
            raise ValueError("CFBD_API_KEY is not set in environment variables")

        # Configure API key authorization
        configuration = cfbd.Configuration()
        configuration.api_key['Authorization'] = CFBD_API_KEY
        configuration.api_key_prefix['Authorization'] = 'Bearer'

        # Create API clients for different endpoints
        self.games_api = cfbd.GamesApi(cfbd.ApiClient(configuration))
        self.teams_api = cfbd.TeamsApi(cfbd.ApiClient(configuration))
        self.plays_api = cfbd.PlaysApi(cfbd.ApiClient(configuration))
        self.drives_api = cfbd.DrivesApi(cfbd.ApiClient(configuration))
        self.conferences_api = cfbd.ConferencesApi(cfbd.ApiClient(configuration))
        self.coaches_api = cfbd.CoachesApi(cfbd.ApiClient(configuration))
        self.venues_api = cfbd.VenuesApi(cfbd.ApiClient(configuration))
        
        logger.info("CFBD API client initialized")

    def _init_call_tracking(self):
        """Initialize API call tracking."""
        if API_CALL_LOG.exists():
            try:
                with open(API_CALL_LOG, 'r') as f:
                    self.call_log = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse API call log file: {API_CALL_LOG}")
                self.call_log = {"calls": []}
        else:
            self.call_log = {"calls": []}

    def _update_call_log(self, endpoint, params):
        """
        Update the API call log with a new call.
        
        Args:
            endpoint (str): The API endpoint called.
            params (dict): The parameters used in the call.
        """
        now = datetime.now()
        call_info = {
            "timestamp": now.isoformat(),
            "endpoint": endpoint,
            "params": params,
        }
        self.call_log["calls"].append(call_info)
        
        # Save the updated call log
        with open(API_CALL_LOG, 'w') as f:
            json.dump(self.call_log, f, indent=2)

    def _get_cache_key(self, endpoint, params):
        """
        Generate a cache key for an API call.
        
        Args:
            endpoint (str): The API endpoint.
            params (dict): The parameters for the API call.
            
        Returns:
            str: A cache key string.
        """
        # Convert params to a sorted, string representation for consistent hashing
        param_str = json.dumps(params, sort_keys=True)
        # Create a hash of the endpoint and parameters
        hash_obj = hashlib.md5(f"{endpoint}:{param_str}".encode())
        return hash_obj.hexdigest()

    def _get_from_cache(self, endpoint, params):
        """
        Get a response from the cache if it exists.
        
        Args:
            endpoint (str): The API endpoint.
            params (dict): The parameters for the API call.
            
        Returns:
            dict or None: The cached response or None if not found.
        """
        if not self.use_cache:
            return None
            
        cache_key = self._get_cache_key(endpoint, params)
        cache_file = API_CACHE_DIR / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                logger.debug(f"Cache hit for {endpoint}")
                return cached_data
            except json.JSONDecodeError:
                logger.warning(f"Could not parse cache file: {cache_file}")
                return None
        return None

    def _save_to_cache(self, endpoint, params, data):
        """
        Save a response to the cache.
        
        Args:
            endpoint (str): The API endpoint.
            params (dict): The parameters for the API call.
            data: The response data to cache.
        """
        if not self.use_cache:
            return
            
        cache_key = self._get_cache_key(endpoint, params)
        cache_file = API_CACHE_DIR / f"{cache_key}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Cached response for {endpoint}")

    def _rate_limit(self):
        """
        Apply rate limiting to API calls.
        
        Raises:
            APIRateLimitError: If the rate limit would be exceeded.
        """
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < MIN_API_CALL_INTERVAL:
            sleep_time = MIN_API_CALL_INTERVAL - time_since_last_call
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
            
        self.last_call_time = time.time()

    def call_api(self, endpoint, api_method, **params):
        """
        Call the CFBD API with rate limiting and caching.
        
        Args:
            endpoint (str): The API endpoint name for logging and caching.
            api_method (callable): The API method to call.
            **params: Parameters to pass to the API method.
            
        Returns:
            The API response data.
            
        Raises:
            APIRateLimitError: If the rate limit would be exceeded.
        """
        # Check cache first
        cached_data = self._get_from_cache(endpoint, params)
        if cached_data is not None:
            return cached_data
        
        # Apply rate limiting
        self._rate_limit()
        
        # Make the API call
        logger.info(f"Calling CFBD API: {endpoint} with params: {params}")
        response = api_method(**params)
        
        # Update call tracking
        self._update_call_log(endpoint, params)
        
        # Convert response to JSON-serializable format if needed
        if hasattr(response, 'to_dict'):
            # Handle list of objects
            if isinstance(response, list):
                data = [item.to_dict() for item in response]
            else:
                data = response.to_dict()
        else:
            data = response
            
        # Cache the response
        self._save_to_cache(endpoint, params, data)
        
        return data

    # Convenience methods for common API calls
    
    def get_games(self, year, **kwargs):
        """
        Get games for a specific year.
        
        Args:
            year (int): The season year.
            **kwargs: Additional parameters for the API call.
            
        Returns:
            list: List of games.
        """
        return self.call_api(
            "games", 
            self.games_api.get_games, 
            year=year, 
            **kwargs
        )
    
    def get_teams(self, **kwargs):
        """
        Get teams data.
        
        Args:
            **kwargs: Parameters for the API call.
            
        Returns:
            list: List of teams.
        """
        return self.call_api(
            "teams", 
            self.teams_api.get_teams, 
            **kwargs
        )
    
    def get_fbs_teams(self, year=None):
        """
        Get FBS teams for a specific year.
        
        Args:
            year (int, optional): The season year.
            
        Returns:
            list: List of FBS teams.
        """
        params = {}
        if year:
            params['year'] = year
        return self.call_api(
            "teams_fbs", 
            self.teams_api.get_fbs_teams, 
            **params
        )
    
    def get_team_talent(self, **kwargs):
        """
        Get team talent composite rankings.
        
        Args:
            **kwargs: Parameters for the API call.
            
        Returns:
            list: List of team talent rankings.
        """
        return self.call_api(
            "talent", 
            self.teams_api.get_talent, 
            **kwargs
        )
    
    def get_plays(self, year, **kwargs):
        """
        Get plays for games in a specific year.
        
        Args:
            year (int): The season year.
            **kwargs: Additional parameters for the API call.
            
        Returns:
            list: List of plays.
        """
        return self.call_api(
            "plays", 
            self.plays_api.get_plays, 
            year=year, 
            **kwargs
        )
    
    def get_play_types(self):
        """
        Get all play types.
        
        Returns:
            list: List of play types.
        """
        return self.call_api(
            "play_types", 
            self.plays_api.get_play_types
        )
    
    def get_drives(self, year, **kwargs):
        """
        Get drives for games in a specific year.
        
        Args:
            year (int): The season year.
            **kwargs: Additional parameters for the API call.
            
        Returns:
            list: List of drives.
        """
        return self.call_api(
            "drives", 
            self.drives_api.get_drives, 
            year=year, 
            **kwargs
        )
    
    def get_conferences(self, **kwargs):
        """
        Get conferences data.
        
        Args:
            **kwargs: Parameters for the API call.
            
        Returns:
            list: List of conferences.
        """
        return self.call_api(
            "conferences", 
            self.conferences_api.get_conferences, 
            **kwargs
        )
    
    def get_coaches(self, **kwargs):
        """
        Get coaches data.
        
        Args:
            **kwargs: Parameters for the API call.
            
        Returns:
            list: List of coaches.
        """
        return self.call_api(
            "coaches", 
            self.coaches_api.get_coaches, 
            **kwargs
        )
    
    def get_venues(self, **kwargs):
        """
        Get venues data.
        
        Args:
            **kwargs: Parameters for the API call.
            
        Returns:
            list: List of venues.
        """
        return self.call_api(
            "venues", 
            self.venues_api.get_venues, 
            **kwargs
        )
