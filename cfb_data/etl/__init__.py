"""ETL modules for loading data from the CFBD API to BigQuery."""

from cfb_data.etl.games import GamesETL
from cfb_data.etl.teams import TeamsETL, TeamsFbsETL, TeamTalentETL
from cfb_data.etl.plays import PlaysETL, PlayTypesETL
from cfb_data.etl.drives import DrivesETL
from cfb_data.etl.conferences import ConferencesETL
from cfb_data.etl.venues import VenuesETL
from cfb_data.etl.coaches import CoachesETL
from cfb_data.config import TABLES


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
        TABLES["games"]: GamesETL(api_client, bq_client),
        TABLES["teams"]: TeamsETL(api_client, bq_client),
        TABLES["teams_fbs"]: TeamsFbsETL(api_client, bq_client),
        TABLES["talent"]: TeamTalentETL(api_client, bq_client),
        TABLES["plays"]: PlaysETL(api_client, bq_client),
        TABLES["play_types"]: PlayTypesETL(api_client, bq_client),
        TABLES["drives"]: DrivesETL(api_client, bq_client),
        TABLES["conferences"]: ConferencesETL(api_client, bq_client),
        TABLES["venues"]: VenuesETL(api_client, bq_client),
        TABLES["coaches"]: CoachesETL(api_client, bq_client),
    }

# Create a function to run ETL for a specific table
def run_etl_for_table(table_name, **kwargs):
    """
    Run the ETL process for a specific table.
    
    Args:
        table_name: The name of the table to run ETL for.
        **kwargs: Additional parameters for the ETL process.
    """
    etl_instances = create_etl_instances()
    if table_name in etl_instances:
        etl_instances[table_name].run(**kwargs)
    else:
        raise ValueError(f"No ETL process defined for table {table_name}")

# Create a function to run historical ETL for a specific table
def run_historical_etl_for_table(table_name, **kwargs):
    """
    Run the historical ETL process for a specific table.
    
    Args:
        table_name: The name of the table to run ETL for.
        **kwargs: Additional parameters for the ETL process.
    """
    etl_instances = create_etl_instances()
    if table_name in etl_instances:
        etl_instances[table_name].run_historical(**kwargs)
    else:
        raise ValueError(f"No ETL process defined for table {table_name}")

# Create a function to run ETL for all tables
def run_etl_for_all_tables(**kwargs):
    """
    Run the ETL process for all tables.
    
    Args:
        **kwargs: Additional parameters for the ETL process.
    """
    etl_instances = create_etl_instances()
    for table_name, etl in etl_instances.items():
        etl.run(**kwargs)

# Create a function to run historical ETL for all tables
def run_historical_etl_for_all_tables(**kwargs):
    """
    Run the historical ETL process for all tables.
    
    Args:
        **kwargs: Additional parameters for the ETL process.
    """
    etl_instances = create_etl_instances()
    for table_name, etl in etl_instances.items():
        etl.run_historical(**kwargs)
