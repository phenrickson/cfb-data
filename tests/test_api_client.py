"""Tests for the API client module."""

import json
import os
import time
from pathlib import Path

import pytest
from unittest.mock import MagicMock, patch, mock_open

from cfb_data.api_client import CFBDApiClient


@pytest.fixture
def mock_cfbd_config():
    """Create a mock CFBD configuration."""
    with patch("cfb_data.api_client.CFBD_API_KEY", "test_api_key"), \
         patch("cfb_data.api_client.MIN_API_CALL_INTERVAL", 0.1), \
         patch("cfb_data.api_client.API_CACHE_DIR", Path("/tmp/api_cache")), \
         patch("cfb_data.api_client.API_CALL_LOG", Path("/tmp/api_call_log.json")):
        yield


@pytest.fixture
def mock_cfbd_api():
    """Create a mock CFBD API."""
    with patch("cfb_data.api_client.cfbd") as mock_cfbd:
        # Mock the Configuration class
        mock_config = MagicMock()
        mock_cfbd.Configuration.return_value = mock_config
        
        # Mock the ApiClient class
        mock_api_client = MagicMock()
        mock_cfbd.ApiClient.return_value = mock_api_client
        
        # Mock the API classes
        mock_games_api = MagicMock()
        mock_teams_api = MagicMock()
        mock_plays_api = MagicMock()
        mock_drives_api = MagicMock()
        mock_conferences_api = MagicMock()
        mock_coaches_api = MagicMock()
        mock_venues_api = MagicMock()
        
        mock_cfbd.GamesApi.return_value = mock_games_api
        mock_cfbd.TeamsApi.return_value = mock_teams_api
        mock_cfbd.PlaysApi.return_value = mock_plays_api
        mock_cfbd.DrivesApi.return_value = mock_drives_api
        mock_cfbd.ConferencesApi.return_value = mock_conferences_api
        mock_cfbd.CoachesApi.return_value = mock_coaches_api
        mock_cfbd.VenuesApi.return_value = mock_venues_api
        
        # Set up mock responses
        mock_games_api.get_games.return_value = [
            {"id": 1, "season": 2023, "week": 1, "home_team": "Team A", "away_team": "Team B"}
        ]
        mock_teams_api.get_teams.return_value = [
            {"id": 1, "school": "Team A", "mascot": "Mascot A"}
        ]
        
        yield mock_cfbd


@pytest.fixture
def api_client(mock_cfbd_config, mock_cfbd_api):
    """Create an API client instance."""
    # Mock the Path.exists and Path.mkdir methods
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.mkdir"):
        # Mock the open function for reading the call log
        with patch("builtins.open", mock_open(read_data='{"calls": []}')):
            client = CFBDApiClient(use_cache=True)
            yield client


def test_init_api_client(mock_cfbd_config, mock_cfbd_api):
    """Test initializing the API client."""
    # Mock the Path.exists and Path.mkdir methods
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.mkdir"):
        # Mock the open function for reading the call log
        with patch("builtins.open", mock_open(read_data='{"calls": []}')):
            client = CFBDApiClient()
            
            # Verify the API key was set
            assert mock_cfbd_api.Configuration.return_value.api_key["Authorization"] == "test_api_key"
            assert mock_cfbd_api.Configuration.return_value.api_key_prefix["Authorization"] == "Bearer"
            
            # Verify the API clients were created
            assert mock_cfbd_api.GamesApi.called
            assert mock_cfbd_api.TeamsApi.called
            assert mock_cfbd_api.PlaysApi.called
            assert mock_cfbd_api.DrivesApi.called
            assert mock_cfbd_api.ConferencesApi.called
            assert mock_cfbd_api.CoachesApi.called
            assert mock_cfbd_api.VenuesApi.called


def test_init_call_tracking(mock_cfbd_config, mock_cfbd_api):
    """Test initializing call tracking."""
    # Mock the Path.exists method to return True
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.mkdir"):
        # Mock the open function for reading the call log
        with patch("builtins.open", mock_open(read_data='{"calls": [{"timestamp": "2023-01-01T00:00:00", "endpoint": "test", "params": {}}]}')):
            client = CFBDApiClient()
            
            # Verify the call log was loaded
            assert len(client.call_log["calls"]) == 1
            assert client.call_log["calls"][0]["endpoint"] == "test"


def test_update_call_log(api_client):
    """Test updating the call log."""
    # Mock the open function for writing the call log
    with patch("builtins.open", mock_open()) as mock_file:
        api_client._update_call_log("test_endpoint", {"param": "value"})
        
        # Verify the call log was updated
        assert len(api_client.call_log["calls"]) == 1
        assert api_client.call_log["calls"][0]["endpoint"] == "test_endpoint"
        assert api_client.call_log["calls"][0]["params"] == {"param": "value"}
        
        # Verify the call log was written to file
        mock_file.assert_called_once()
        mock_file().write.assert_called_once()


def test_get_cache_key(api_client):
    """Test generating a cache key."""
    # Generate a cache key
    cache_key = api_client._get_cache_key("test_endpoint", {"param": "value"})
    
    # Verify the cache key is a string
    assert isinstance(cache_key, str)
    assert len(cache_key) > 0


def test_get_from_cache_hit(api_client):
    """Test getting a response from the cache (cache hit)."""
    # Mock the Path.exists method to return True
    with patch("pathlib.Path.exists", return_value=True):
        # Mock the open function for reading the cache
        with patch("builtins.open", mock_open(read_data='{"id": 1, "name": "Test"}')):
            # Get from cache
            cached_data = api_client._get_from_cache("test_endpoint", {"param": "value"})
            
            # Verify the cached data was returned
            assert cached_data == {"id": 1, "name": "Test"}


def test_get_from_cache_miss(api_client):
    """Test getting a response from the cache (cache miss)."""
    # Mock the Path.exists method to return False
    with patch("pathlib.Path.exists", return_value=False):
        # Get from cache
        cached_data = api_client._get_from_cache("test_endpoint", {"param": "value"})
        
        # Verify None was returned
        assert cached_data is None


def test_save_to_cache(api_client):
    """Test saving a response to the cache."""
    # Mock the open function for writing the cache
    with patch("builtins.open", mock_open()) as mock_file:
        # Save to cache
        api_client._save_to_cache("test_endpoint", {"param": "value"}, {"id": 1, "name": "Test"})
        
        # Verify the cache was written to file
        mock_file.assert_called_once()
        mock_file().write.assert_called_once()


@patch("cfb_data.api_client.time")
def test_rate_limit(mock_time, api_client):
    """Test rate limiting."""
    # Set up the mock time
    mock_time.time.side_effect = [0, 0.05]  # First call returns 0, second call returns 0.05
    
    # Set the last call time
    api_client.last_call_time = 0
    
    # Apply rate limiting
    api_client._rate_limit()
    
    # Verify time.sleep was called with the correct value
    # MIN_API_CALL_INTERVAL is 0.1, so we should sleep for 0.1 - 0.05 = 0.05
    mock_time.sleep.assert_called_once_with(0.05)


def test_call_api_cached(api_client):
    """Test calling the API with a cached response."""
    # Mock the _get_from_cache method to return a cached response
    with patch.object(api_client, "_get_from_cache", return_value={"id": 1, "name": "Test"}):
        # Mock the _rate_limit and _update_call_log methods
        with patch.object(api_client, "_rate_limit") as mock_rate_limit, \
             patch.object(api_client, "_update_call_log") as mock_update_call_log, \
             patch.object(api_client, "_save_to_cache") as mock_save_to_cache:
            # Call the API
            response = api_client.call_api("test_endpoint", lambda: None)
            
            # Verify the cached response was returned
            assert response == {"id": 1, "name": "Test"}
            
            # Verify the rate limiting and call tracking methods were not called
            mock_rate_limit.assert_not_called()
            mock_update_call_log.assert_not_called()
            mock_save_to_cache.assert_not_called()


def test_call_api_uncached(api_client):
    """Test calling the API without a cached response."""
    # Mock the _get_from_cache method to return None
    with patch.object(api_client, "_get_from_cache", return_value=None):
        # Mock the _rate_limit, _update_call_log, and _save_to_cache methods
        with patch.object(api_client, "_rate_limit") as mock_rate_limit, \
             patch.object(api_client, "_update_call_log") as mock_update_call_log, \
             patch.object(api_client, "_save_to_cache") as mock_save_to_cache:
            # Create a mock API method
            mock_api_method = MagicMock(return_value={"id": 1, "name": "Test"})
            
            # Call the API
            response = api_client.call_api("test_endpoint", mock_api_method, param="value")
            
            # Verify the API method was called
            mock_api_method.assert_called_once_with(param="value")
            
            # Verify the rate limiting and call tracking methods were called
            mock_rate_limit.assert_called_once()
            mock_update_call_log.assert_called_once_with("test_endpoint", {"param": "value"})
            mock_save_to_cache.assert_called_once_with("test_endpoint", {"param": "value"}, {"id": 1, "name": "Test"})
            
            # Verify the response was returned
            assert response == {"id": 1, "name": "Test"}


def test_get_games(api_client, mock_cfbd_api):
    """Test getting games data."""
    # Mock the call_api method
    with patch.object(api_client, "call_api") as mock_call_api:
        # Call the get_games method
        api_client.get_games(2023, week=1)
        
        # Verify the call_api method was called with the correct parameters
        mock_call_api.assert_called_once_with(
            "games",
            api_client.games_api.get_games,
            year=2023,
            week=1
        )


def test_get_teams(api_client, mock_cfbd_api):
    """Test getting teams data."""
    # Mock the call_api method
    with patch.object(api_client, "call_api") as mock_call_api:
        # Call the get_teams method
        api_client.get_teams(conference="SEC")
        
        # Verify the call_api method was called with the correct parameters
        mock_call_api.assert_called_once_with(
            "teams",
            api_client.teams_api.get_teams,
            conference="SEC"
        )
