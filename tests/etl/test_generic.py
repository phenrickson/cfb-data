"""Tests for the generic ETL module."""

import pytest
from unittest.mock import MagicMock, patch

from cfb_data.etl.generic import GenericETL, transform_games, transform_teams


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = MagicMock()
    client.get_test_data = MagicMock(return_value=[
        {"id": 1, "name": "Test 1"},
        {"id": 2, "name": "Test 2"},
    ])
    client.get_seasonal_data = MagicMock(return_value=[
        {"id": 1, "season": 2023, "name": "Test 1"},
        {"id": 2, "season": 2023, "name": "Test 2"},
    ])
    return client


@pytest.fixture
def mock_bq_client():
    """Create a mock BigQuery client."""
    return MagicMock()


@pytest.fixture
def etl(mock_api_client, mock_bq_client):
    """Create a test ETL instance."""
    return GenericETL(
        table_name="test_table",
        api_method="get_test_data",
        is_seasonal=False,
        transform_func=lambda x: x,  # Identity function
        api_client=mock_api_client,
        bq_client=mock_bq_client,
    )


@pytest.fixture
def seasonal_etl(mock_api_client, mock_bq_client):
    """Create a seasonal test ETL instance."""
    return GenericETL(
        table_name="test_seasonal_table",
        api_method="get_seasonal_data",
        is_seasonal=True,
        transform_func=lambda x: x,  # Identity function
        api_client=mock_api_client,
        bq_client=mock_bq_client,
    )


def test_extract_non_seasonal(etl, mock_api_client):
    """Test extracting non-seasonal data."""
    # Call the extract method
    data = etl.extract()
    
    # Verify the API method was called
    mock_api_client.get_test_data.assert_called_once_with()
    
    # Verify the data was returned
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[1]["name"] == "Test 2"


def test_extract_seasonal(seasonal_etl, mock_api_client):
    """Test extracting seasonal data."""
    # Call the extract method with a specific year
    data = seasonal_etl.extract(year=2023)
    
    # Verify the API method was called with the year parameter
    mock_api_client.get_seasonal_data.assert_called_once_with(year=2023)
    
    # Verify the data was returned
    assert len(data) == 2
    assert data[0]["season"] == 2023


def test_transform(mock_api_client, mock_bq_client):
    """Test transforming data."""
    # Create test data
    test_data = [
        {"id": 1, "name": "Test 1"},
        {"id": 2, "name": "Test 2"},
    ]
    
    # Create a transform function that adds a field
    def transform_func(data):
        return [
            {**item, "transformed": True}
            for item in data
        ]
    
    # Create an ETL instance with the transform function
    transform_etl = GenericETL(
        table_name="test_transform_table",
        api_method="get_test_data",
        transform_func=transform_func,
        api_client=mock_api_client,
        bq_client=mock_bq_client,
    )
    
    # Call the transform method
    transformed_data = transform_etl.transform(test_data)
    
    # Verify the data was transformed
    assert len(transformed_data) == 2
    assert transformed_data[0]["transformed"] is True
    assert transformed_data[1]["transformed"] is True


def test_load(etl, mock_bq_client):
    """Test loading data."""
    # Create test data
    test_data = [
        {"id": 1, "name": "Test 1"},
        {"id": 2, "name": "Test 2"},
    ]
    
    # Call the load method
    etl.load(test_data, write_disposition="WRITE_TRUNCATE")
    
    # Verify the BigQuery client was called
    mock_bq_client.load_data_from_json.assert_called_once_with(
        "test_table", test_data, "WRITE_TRUNCATE"
    )


def test_run(etl, mock_api_client, mock_bq_client):
    """Test running the ETL process."""
    # Call the run method
    etl.run(write_disposition="WRITE_TRUNCATE")
    
    # Verify the API method was called
    mock_api_client.get_test_data.assert_called_once_with()
    
    # Verify the BigQuery client was called
    mock_bq_client.load_data_from_json.assert_called_once()


@patch("cfb_data.etl.generic.time")
def test_run_historical_non_seasonal(mock_time, etl, mock_api_client, mock_bq_client):
    """Test running the historical ETL process for non-seasonal data."""
    # Call the run_historical method
    etl.run_historical(write_disposition="WRITE_TRUNCATE")
    
    # Verify the API method was called
    mock_api_client.get_test_data.assert_called_once_with()
    
    # Verify the BigQuery client was called
    mock_bq_client.load_data_from_json.assert_called_once()
    
    # Verify time.sleep was not called (no need for rate limiting)
    mock_time.sleep.assert_not_called()


@patch("cfb_data.etl.generic.time")
def test_run_historical_seasonal(mock_time, seasonal_etl, mock_api_client, mock_bq_client):
    """Test running the historical ETL process for seasonal data."""
    # Call the run_historical method with a specific range
    seasonal_etl.run_historical(
        start_season=2022,
        end_season=2023,
        write_disposition="WRITE_TRUNCATE",
    )
    
    # Verify the API method was called for each season
    assert mock_api_client.get_seasonal_data.call_count == 2
    
    # Verify the BigQuery client was called
    mock_bq_client.load_data_from_json.assert_called_once()
    
    # Verify time.sleep was called for rate limiting
    assert mock_time.sleep.call_count == 1


def test_transform_games():
    """Test transforming games data."""
    # Create test data
    test_data = [
        {
            "id": 1,
            "season": 2023,
            "week": 1,
            "season_type": "regular",
            "start_date": "2023-09-01T00:00:00Z",
            "neutral_site": False,
            "conference_game": True,
            "attendance": 80000,
            "venue_id": 1,
            "venue": "Test Stadium",
            "home_team": "Team A",
            "home_conference": "Conference A",
            "home_points": 28,
            "away_team": "Team B",
            "away_conference": "Conference B",
            "away_points": 21,
            "extra_field": "This should be removed",
        }
    ]
    
    # Call the transform function
    transformed_data = transform_games(test_data)
    
    # Verify the data was transformed correctly
    assert len(transformed_data) == 1
    assert transformed_data[0]["id"] == 1
    assert transformed_data[0]["home_team"] == "Team A"
    assert transformed_data[0]["away_points"] == 21
    assert "extra_field" not in transformed_data[0]


def test_transform_teams():
    """Test transforming teams data."""
    # Create test data
    test_data = [
        {
            "id": 1,
            "school": "Test University",
            "mascot": "Test Mascot",
            "abbreviation": "TU",
            "alt_name_1": "Test U",
            "alt_name_2": None,
            "alt_name_3": None,
            "conference": "Test Conference",
            "division": "Test Division",
            "color": "#FF0000",
            "alt_color": "#0000FF",
            "logos": ["https://example.com/logo.png"],
            "location": {
                "venue_id": 1,
                "name": "Test Stadium",
                "city": "Test City",
                "state": "TS",
                "zip": "12345",
                "country_code": "US",
                "timezone": "America/New_York",
                "latitude": 40.0,
                "longitude": -80.0,
                "elevation": 100.0,
                "capacity": 80000,
                "year_constructed": 2000,
                "grass": True,
                "dome": False,
            },
            "extra_field": "This should be removed",
        }
    ]
    
    # Call the transform function
    transformed_data = transform_teams(test_data)
    
    # Verify the data was transformed correctly
    assert len(transformed_data) == 1
    assert transformed_data[0]["id"] == 1
    assert transformed_data[0]["school"] == "Test University"
    assert transformed_data[0]["conference"] == "Test Conference"
    assert "location" in transformed_data[0]
    assert "extra_field" not in transformed_data[0]
