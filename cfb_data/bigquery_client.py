import json
from pathlib import Path

from google.cloud import bigquery
from google.api_core.exceptions import NotFound
from loguru import logger

from cfb_data.config import (
    GCP_PROJECT_ID,
    BQ_DATASET_ID,
    BQ_LOCATION,
    TABLES,
)


class BigQueryClient:
    """Client for interacting with Google BigQuery."""

    def __init__(self):
        """Initialize the BigQuery client."""
        if not GCP_PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID is not set in environment variables")
            
        self.client = bigquery.Client(project=GCP_PROJECT_ID)
        self.dataset_id = BQ_DATASET_ID
        self.dataset_ref = self.client.dataset(self.dataset_id)
        
        logger.info(f"BigQuery client initialized for project: {GCP_PROJECT_ID}")

    def dataset_exists(self):
        """
        Check if the dataset exists.
        
        Returns:
            bool: True if the dataset exists, False otherwise.
        """
        try:
            self.client.get_dataset(self.dataset_ref)
            return True
        except NotFound:
            return False

    def create_dataset(self):
        """
        Create the dataset if it doesn't exist.
        
        Returns:
            google.cloud.bigquery.Dataset: The created or existing dataset.
        """
        if self.dataset_exists():
            logger.info(f"Dataset {self.dataset_id} already exists")
            return self.client.get_dataset(self.dataset_ref)
            
        dataset = bigquery.Dataset(self.dataset_ref)
        dataset.location = BQ_LOCATION
        dataset.description = "College Football Data from CFBD API"
        
        dataset = self.client.create_dataset(dataset)
        logger.success(f"Dataset {self.dataset_id} created")
        return dataset

    def table_exists(self, table_name):
        """
        Check if a table exists in the dataset.
        
        Args:
            table_name (str): The name of the table.
            
        Returns:
            bool: True if the table exists, False otherwise.
        """
        table_ref = self.dataset_ref.table(table_name)
        try:
            self.client.get_table(table_ref)
            return True
        except NotFound:
            return False

    def create_table(self, table_name, schema):
        """
        Create a table in the dataset if it doesn't exist.
        
        Args:
            table_name (str): The name of the table.
            schema (list): The schema for the table.
            
        Returns:
            google.cloud.bigquery.Table: The created or existing table.
        """
        if self.table_exists(table_name):
            logger.info(f"Table {table_name} already exists")
            return self.client.get_table(self.dataset_ref.table(table_name))
            
        table_ref = self.dataset_ref.table(table_name)
        table = bigquery.Table(table_ref, schema=schema)
        
        table = self.client.create_table(table)
        logger.success(f"Table {table_name} created")
        return table

    def load_data_from_json(self, table_name, json_data, write_disposition="WRITE_APPEND"):
        """
        Load data from a JSON object into a BigQuery table.
        
        Args:
            table_name (str): The name of the table.
            json_data (list): The JSON data to load.
            write_disposition (str): The write disposition for the job.
                Can be WRITE_TRUNCATE, WRITE_APPEND, or WRITE_EMPTY.
                
        Returns:
            google.cloud.bigquery.job.LoadJob: The load job.
        """
        if not json_data:
            logger.warning(f"No data to load into {table_name}")
            return None
            
        # Ensure the dataset exists
        if not self.dataset_exists():
            self.create_dataset()
            
        table_ref = self.dataset_ref.table(table_name)
        
        # Create a temporary JSON file
        temp_file = Path(f"/tmp/{table_name}_{hash(str(json_data))}.json")
        with open(temp_file, 'w') as f:
            for item in json_data:
                f.write(json.dumps(item) + '\n')
        
        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=getattr(bigquery.WriteDisposition, write_disposition),
            autodetect=True,  # Auto-detect schema
        )
        
        # Load the data
        with open(temp_file, 'rb') as f:
            load_job = self.client.load_table_from_file(
                f, table_ref, job_config=job_config
            )
            
        # Wait for the job to complete
        load_job.result()
        
        # Clean up the temporary file
        temp_file.unlink()
        
        logger.success(
            f"Loaded {len(json_data)} rows into {table_name} "
            f"with disposition {write_disposition}"
        )
        
        return load_job

    def query(self, query):
        """
        Execute a query on BigQuery.
        
        Args:
            query (str): The SQL query to execute.
            
        Returns:
            google.cloud.bigquery.table.RowIterator: The query results.
        """
        query_job = self.client.query(query)
        return query_job.result()

    def get_table_schema(self, table_name):
        """
        Get the schema for a table.
        
        Args:
            table_name (str): The name of the table.
            
        Returns:
            list: The schema for the table.
        """
        if not self.table_exists(table_name):
            logger.warning(f"Table {table_name} does not exist")
            return None
            
        table = self.client.get_table(self.dataset_ref.table(table_name))
        return table.schema

    def get_table_row_count(self, table_name):
        """
        Get the number of rows in a table.
        
        Args:
            table_name (str): The name of the table.
            
        Returns:
            int: The number of rows in the table.
        """
        if not self.table_exists(table_name):
            logger.warning(f"Table {table_name} does not exist")
            return 0
            
        query = f"SELECT COUNT(*) as count FROM `{self.dataset_id}.{table_name}`"
        results = self.query(query)
        
        for row in results:
            return row.count
            
        return 0


# Schema definitions for each table
# These can be adjusted based on the actual API response structure

GAMES_SCHEMA = [
    bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("season", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("week", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("season_type", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("start_date", "TIMESTAMP"),
    bigquery.SchemaField("neutral_site", "BOOLEAN"),
    bigquery.SchemaField("conference_game", "BOOLEAN"),
    bigquery.SchemaField("attendance", "INTEGER"),
    bigquery.SchemaField("venue_id", "INTEGER"),
    bigquery.SchemaField("venue", "STRING"),
    bigquery.SchemaField("home_team", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("home_conference", "STRING"),
    bigquery.SchemaField("home_points", "INTEGER"),
    bigquery.SchemaField("away_team", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("away_conference", "STRING"),
    bigquery.SchemaField("away_points", "INTEGER"),
]

TEAMS_SCHEMA = [
    bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("school", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("mascot", "STRING"),
    bigquery.SchemaField("abbreviation", "STRING"),
    bigquery.SchemaField("alt_name_1", "STRING"),
    bigquery.SchemaField("alt_name_2", "STRING"),
    bigquery.SchemaField("alt_name_3", "STRING"),
    bigquery.SchemaField("conference", "STRING"),
    bigquery.SchemaField("division", "STRING"),
    bigquery.SchemaField("color", "STRING"),
    bigquery.SchemaField("alt_color", "STRING"),
    bigquery.SchemaField("logos", "STRING", mode="REPEATED"),
    bigquery.SchemaField("location", "RECORD", fields=[
        bigquery.SchemaField("venue_id", "INTEGER"),
        bigquery.SchemaField("name", "STRING"),
        bigquery.SchemaField("city", "STRING"),
        bigquery.SchemaField("state", "STRING"),
        bigquery.SchemaField("zip", "STRING"),
        bigquery.SchemaField("country_code", "STRING"),
        bigquery.SchemaField("timezone", "STRING"),
        bigquery.SchemaField("latitude", "FLOAT"),
        bigquery.SchemaField("longitude", "FLOAT"),
        bigquery.SchemaField("elevation", "FLOAT"),
        bigquery.SchemaField("capacity", "INTEGER"),
        bigquery.SchemaField("year_constructed", "INTEGER"),
        bigquery.SchemaField("grass", "BOOLEAN"),
        bigquery.SchemaField("dome", "BOOLEAN"),
    ]),
]

PLAYS_SCHEMA = [
    bigquery.SchemaField("game_id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("drive_id", "INTEGER"),
    bigquery.SchemaField("drive_number", "INTEGER"),
    bigquery.SchemaField("period", "INTEGER"),
    bigquery.SchemaField("clock", "RECORD", fields=[
        bigquery.SchemaField("minutes", "INTEGER"),
        bigquery.SchemaField("seconds", "INTEGER"),
    ]),
    bigquery.SchemaField("offense_team", "STRING"),
    bigquery.SchemaField("offense_conference", "STRING"),
    bigquery.SchemaField("defense_team", "STRING"),
    bigquery.SchemaField("defense_conference", "STRING"),
    bigquery.SchemaField("yard_line", "INTEGER"),
    bigquery.SchemaField("yards_to_goal", "INTEGER"),
    bigquery.SchemaField("down", "INTEGER"),
    bigquery.SchemaField("distance", "INTEGER"),
    bigquery.SchemaField("play_type", "STRING"),
    bigquery.SchemaField("play_text", "STRING"),
    bigquery.SchemaField("yards_gained", "INTEGER"),
]

DRIVES_SCHEMA = [
    bigquery.SchemaField("game_id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("drive_number", "INTEGER"),
    bigquery.SchemaField("offense", "STRING"),
    bigquery.SchemaField("offense_conference", "STRING"),
    bigquery.SchemaField("defense", "STRING"),
    bigquery.SchemaField("defense_conference", "STRING"),
    bigquery.SchemaField("scoring", "BOOLEAN"),
    bigquery.SchemaField("start_period", "INTEGER"),
    bigquery.SchemaField("start_clock", "RECORD", fields=[
        bigquery.SchemaField("minutes", "INTEGER"),
        bigquery.SchemaField("seconds", "INTEGER"),
    ]),
    bigquery.SchemaField("start_yards_to_goal", "INTEGER"),
    bigquery.SchemaField("end_period", "INTEGER"),
    bigquery.SchemaField("end_clock", "RECORD", fields=[
        bigquery.SchemaField("minutes", "INTEGER"),
        bigquery.SchemaField("seconds", "INTEGER"),
    ]),
    bigquery.SchemaField("end_yards_to_goal", "INTEGER"),
    bigquery.SchemaField("plays", "INTEGER"),
    bigquery.SchemaField("yards", "INTEGER"),
    bigquery.SchemaField("drive_result", "STRING"),
]

CONFERENCES_SCHEMA = [
    bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("short_name", "STRING"),
    bigquery.SchemaField("abbreviation", "STRING"),
    bigquery.SchemaField("classification", "STRING"),
]

VENUES_SCHEMA = [
    bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("city", "STRING"),
    bigquery.SchemaField("state", "STRING"),
    bigquery.SchemaField("zip", "STRING"),
    bigquery.SchemaField("country_code", "STRING"),
    bigquery.SchemaField("timezone", "STRING"),
    bigquery.SchemaField("latitude", "FLOAT"),
    bigquery.SchemaField("longitude", "FLOAT"),
    bigquery.SchemaField("elevation", "FLOAT"),
    bigquery.SchemaField("capacity", "INTEGER"),
    bigquery.SchemaField("year_constructed", "INTEGER"),
    bigquery.SchemaField("grass", "BOOLEAN"),
    bigquery.SchemaField("dome", "BOOLEAN"),
]

COACHES_SCHEMA = [
    bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("first_name", "STRING"),
    bigquery.SchemaField("last_name", "STRING"),
    bigquery.SchemaField("seasons", "RECORD", mode="REPEATED", fields=[
        bigquery.SchemaField("school", "STRING"),
        bigquery.SchemaField("year", "INTEGER"),
        bigquery.SchemaField("games", "INTEGER"),
        bigquery.SchemaField("wins", "INTEGER"),
        bigquery.SchemaField("losses", "INTEGER"),
        bigquery.SchemaField("ties", "INTEGER"),
        bigquery.SchemaField("preseason_rank", "INTEGER"),
        bigquery.SchemaField("postseason_rank", "INTEGER"),
        bigquery.SchemaField("srs", "FLOAT"),
        bigquery.SchemaField("sp_overall", "FLOAT"),
        bigquery.SchemaField("sp_offense", "FLOAT"),
        bigquery.SchemaField("sp_defense", "FLOAT"),
    ]),
]

TALENT_SCHEMA = [
    bigquery.SchemaField("year", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("school", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("talent", "FLOAT"),
]

PLAY_TYPES_SCHEMA = [
    bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("text", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("abbreviation", "STRING"),
]

# Map table names to their schemas
TABLE_SCHEMAS = {
    TABLES["games"]: GAMES_SCHEMA,
    TABLES["teams"]: TEAMS_SCHEMA,
    TABLES["teams_fbs"]: TEAMS_SCHEMA,  # Same schema as teams
    TABLES["plays"]: PLAYS_SCHEMA,
    TABLES["drives"]: DRIVES_SCHEMA,
    TABLES["conferences"]: CONFERENCES_SCHEMA,
    TABLES["venues"]: VENUES_SCHEMA,
    TABLES["coaches"]: COACHES_SCHEMA,
    TABLES["talent"]: TALENT_SCHEMA,
    TABLES["play_types"]: PLAY_TYPES_SCHEMA,
}


def setup_bigquery():
    """
    Set up the BigQuery dataset and tables.
    
    Returns:
        BigQueryClient: The BigQuery client.
    """
    client = BigQueryClient()
    
    # Create the dataset
    client.create_dataset()
    
    # Create tables
    for table_name, schema in TABLE_SCHEMAS.items():
        client.create_table(table_name, schema)
        
    return client
