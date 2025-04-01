"""ETL modules for loading data from the CFBD API to BigQuery."""

from cfb_data.etl.generic import (
    GenericETL,
    create_etl_instances,
    transform_games,
    transform_teams,
    transform_talent,
    transform_plays,
    transform_play_types,
    transform_drives,
    transform_conferences,
    transform_venues,
    transform_coaches,
)

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
