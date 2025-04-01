
# tasks
- view documentation for possible API endpoints to load from https://api.collegefootballdata.com/api/docs/?url=/api-docs.json
- create BigQuery data warehouse on GCP
- create schemas for tables on BigQuery
- submit API requests to load historical data from past seasons (up to 2024) to data warehouse
- create process for updating data warehouse with new data from current season
- use Makefile for orchestration of tasks
- add project overview to README with architecture diagram
- ensure that API requests do not exceed rate limits (5000 monthly calls) using CFBD_API_KEY

# tables

tables to load from CFBD API

- games
- drives
- plays
- play/types
- teams
- teams/fbs
- talent
- conferences
- venues
- coaches