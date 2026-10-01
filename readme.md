# ProMan Lakehouse Pipeline & Analytics

This repository contains the code and artifacts for an automated cloud ELT pipeline and operational dashboard built for project management tracking (ProMan) using Azure Databricks, Delta Lake, and Auto Loader. 

The pipeline ingests heterogeneous operational data (RDBMS extracts, microservice time-tracking JSONs, and unstructured file sidecars) through a Medallion Lakehouse Architecture (Bronze $\to$ Silver $\to$ Gold) to support project controlling, burndown velocity, and scope creep detection.


---

## Repository Structure

```text
├── dashboard/
│   ├── queries/                       # Standalone SQL queries powering the dashboard datasets
│   ├── dashboard_export.lvdash.json   # Exported Databricks Lakeview/Dashboard definition
│   └── screenshots/                   # Exported visuals and screenshots of dashboard views
│
├── data_generation/                   # Local Python scripts for source data simulation
│   ├── generate_rdbms.py              # Generates initial Day 0 relational tables (CSV)
│   ├── generate_timetracking.py       # Generates baseline Day 0 time tracking logs (JSON)
│   ├── generate_timetracking_next.py  # Simulates stateful Day 1+ incremental time logs
│   ├── simulate_day2_updates.py       # Simulates Day 2 RDBMS task status changes and scope creep
|   ├── upload_to_adls.py              # Uploads files to adls gen 2 data lake storage inside the staging folder
│   └── sample_data/                   # Sample raw files for inspection
│
├── databricks_notebooks/              # Exported PySpark/SQL Lakehouse pipeline notebooks
│   ├── 01_bronze_ingestion.py         # Auto Loader micro-batch ingestion into raw Delta tables
│   ├── 02_silver_transformations.py   # Schema-on-Read, DQ validations, and quarantine routing
│   ├── 03_gold_dimensions_facts.py    # MD5 surrogate key generation, star schema facts/dims
│   └── 04_gold_analytical_marts.py    # Analytical aggregations and historical snapshot facts
│
├── docs/
│   └── data_dictionary.md             # Granular schema specifications and table definitions
│
├── .gitignore
└── README.md