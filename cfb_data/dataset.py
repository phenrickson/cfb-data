import os
from pathlib import Path
from typing import List, Optional

from loguru import logger
import typer

from cfb_data.config import (
    TABLES,
    FIRST_SEASON,
    LAST_SEASON,
    BQ_DATASET_ID,
)
from cfb_data.bigquery_client import setup_bigquery
from cfb_data.etl import (
    run_etl_for_table,
    run_historical_etl_for_table,
    run_etl_for_all_tables,
    run_historical_etl_for_all_tables,
)

app = typer.Typer()


@app.command()
def setup_bigquery_resources():
    """Set up the BigQuery dataset and tables."""
    logger.info("Setting up BigQuery resources...")
    setup_bigquery()
    logger.success("BigQuery resources set up successfully.")


@app.command()
def load_table(
    table_name: str = typer.Argument(..., help="The name of the table to load data for."),
    year: Optional[int] = typer.Option(None, help="The season year to load data for."),
    write_disposition: str = typer.Option(
        "WRITE_APPEND", help="The write disposition for the load job."
    ),
):
    """Load data for a specific table."""
    if table_name not in TABLES.values():
        valid_tables = ", ".join(TABLES.values())
        logger.error(f"Invalid table name: {table_name}. Valid tables are: {valid_tables}")
        raise typer.Exit(1)
        
    logger.info(f"Loading data for table {table_name}...")
    
    kwargs = {"write_disposition": write_disposition}
    if year:
        kwargs["year"] = year
        
    run_etl_for_table(table_name, **kwargs)
    
    logger.success(f"Data loaded for table {table_name}.")


@app.command()
def load_historical_data(
    table_name: str = typer.Argument(..., help="The name of the table to load historical data for."),
    start_season: int = typer.Option(
        FIRST_SEASON, help="The first season to load data for."
    ),
    end_season: int = typer.Option(
        LAST_SEASON, help="The last season to load data for."
    ),
    write_disposition: str = typer.Option(
        "WRITE_TRUNCATE", help="The write disposition for the load job."
    ),
):
    """Load historical data for a specific table."""
    if table_name not in TABLES.values():
        valid_tables = ", ".join(TABLES.values())
        logger.error(f"Invalid table name: {table_name}. Valid tables are: {valid_tables}")
        raise typer.Exit(1)
        
    logger.info(
        f"Loading historical data for table {table_name} "
        f"from {start_season} to {end_season}..."
    )
    
    run_historical_etl_for_table(
        table_name,
        start_season=start_season,
        end_season=end_season,
        write_disposition=write_disposition,
    )
    
    logger.success(
        f"Historical data loaded for table {table_name} "
        f"from {start_season} to {end_season}."
    )


@app.command()
def load_all_tables(
    year: Optional[int] = typer.Option(None, help="The season year to load data for."),
    write_disposition: str = typer.Option(
        "WRITE_APPEND", help="The write disposition for the load job."
    ),
):
    """Load data for all tables."""
    logger.info("Loading data for all tables...")
    
    kwargs = {"write_disposition": write_disposition}
    if year:
        kwargs["year"] = year
        
    run_etl_for_all_tables(**kwargs)
    
    logger.success("Data loaded for all tables.")


@app.command()
def load_all_historical_data(
    start_season: int = typer.Option(
        FIRST_SEASON, help="The first season to load data for."
    ),
    end_season: int = typer.Option(
        LAST_SEASON, help="The last season to load data for."
    ),
    write_disposition: str = typer.Option(
        "WRITE_TRUNCATE", help="The write disposition for the load job."
    ),
):
    """Load historical data for all tables."""
    logger.info(
        f"Loading historical data for all tables "
        f"from {start_season} to {end_season}..."
    )
    
    run_historical_etl_for_all_tables(
        start_season=start_season,
        end_season=end_season,
        write_disposition=write_disposition,
    )
    
    logger.success(
        f"Historical data loaded for all tables "
        f"from {start_season} to {end_season}."
    )


@app.command()
def update_current_season():
    """Update data for the current season."""
    logger.info("Updating data for the current season...")
    
    # Use WRITE_TRUNCATE for the current season to ensure we have the latest data
    run_etl_for_all_tables(
        year=LAST_SEASON,
        write_disposition="WRITE_TRUNCATE",
    )
    
    logger.success("Data updated for the current season.")


if __name__ == "__main__":
    app()
