# ProMan Lakehouse Data Dictionary

This document describes the tables, columns, data types, grains, validation rules, and write strategies implemented by:

- `databricks_notebooks/01_bronze_ingestion.ipynb`
- `databricks_notebooks/02_silver_transformations.ipynb`
- `databricks_notebooks/03_gold_star_schema.ipynb`

The Unity Catalog namespace used by the notebooks is `dbw_proman_lakehouse_01.default`.

## Architectural conventions

- Persistent tables use Delta Lake.
- RDBMS Bronze tables are full daily snapshots written with `overwrite`.
- Time-tracking and document manifests use Auto Loader with `availableNow=True` and `append` mode.
- Silver tables are rebuilt with `overwrite` for each run.
- Gold dimensions, facts, and current-state marts are rebuilt with `overwrite`.
- Historical snapshot tables use `append` mode and are partitioned by `snapshot_date`.
- Dimension surrogate keys are deterministic MD5 hashes of natural identifiers.
- Fact foreign-key lookups use `"-1"` when a dimension lookup is missing.
- Processing metadata uses `_source_file`, `_ingested_at`, `_transformed_at`, `_loaded_at`, and `_updated_at` where created by the notebooks.

## 1. Bronze layer

Bronze tables preserve source data with ingestion metadata. The RDBMS tables are replaceable snapshots; the Auto Loader tables append newly discovered files.

### `bronze_users`

**Grain:** One row per user from the RDBMS CSV snapshot.

| Column | Type in Bronze contract | Description |
|---|---|---|
| `user_id` | Inferred from CSV | Natural user identifier. |
| `full_name` | Inferred from CSV | User's full name. |
| `email` | Inferred from CSV | User email address. |
| `department` | Inferred from CSV | Organizational department. |
| `role` | Inferred from CSV | User role. |
| `hourly_rate` | Inferred from CSV or absent | Optional source hourly rate. |
| `is_active` | Inferred from CSV | Whether the user is active. |
| `_ingested_at` | TIMESTAMP | Time the row was written to Bronze. |
| `_source_file` | STRING | Source file path from `_metadata.file_path`. |

The table is loaded from `staging/rdbms/users.csv` with `mode("overwrite")`.

### `bronze_projects`

**Grain:** One row per project from the RDBMS CSV snapshot.

| Column | Type in Bronze contract | Description |
|---|---|---|
| `project_id` | Inferred from CSV | Natural project identifier. |
| `project_name` | Inferred from CSV | Project name. |
| `status` | Inferred from CSV | Operational project status. |
| `start_date` | Inferred from CSV | Planned project start date. |
| `due_date` | Inferred from CSV | Planned project due date. |
| `budget_hours` | Inferred from CSV | Planned labor-hour budget. |
| `budget_amount` | Inferred from CSV | Planned monetary budget. |
| `_ingested_at` | TIMESTAMP | Time the row was written to Bronze. |
| `_source_file` | STRING | Source file path from `_metadata.file_path`. |

The table is loaded from `staging/rdbms/projects.csv` with `mode("overwrite")`.

### `bronze_tasks`

**Grain:** One row per task from the RDBMS CSV snapshot.

| Column | Type in Bronze contract | Description |
|---|---|---|
| `task_id` | Inferred from CSV | Natural task identifier. |
| `project_id` | Inferred from CSV | Parent project identifier. |
| `assigned_user_id` | Inferred from CSV | Assigned user identifier. |
| `task_name` | Inferred from CSV | Task name. |
| `priority` | Inferred from CSV | Task priority. |
| `status` | Inferred from CSV | Task status. |
| `estimated_hours` | Inferred from CSV | Raw estimated effort. |
| `_ingested_at` | TIMESTAMP | Time the row was written to Bronze. |
| `_source_file` | STRING | Source file path from `_metadata.file_path`. |

The table is loaded from `staging/rdbms/tasks.csv` with `mode("overwrite")`.

### `bronze_timetracking`

**Grain:** One row per time-tracking export payload.

| Column | Type | Description |
|---|---|---|
| `system_name` | STRING | Source microservice name. |
| `export_version` | STRING | Source payload version. |
| `extracted_at` | STRING | Extraction timestamp supplied by the source. |
| `record_count` | INT | Number of log records declared by the source. |
| `logs` | ARRAY<STRUCT> | Nested time-entry records. Each struct contains `entry_id` STRING, `project_id` STRING, `task_id` STRING, `user_id` INT, `date` STRING, `hours_worked` DOUBLE, `progress_pct` DOUBLE, `activity_description` STRING, and `is_billable` BOOLEAN. |
| `_ingested_at` | TIMESTAMP | Auto Loader ingestion timestamp. |
| `_source_file` | STRING | Input file path from `_metadata.file_path`. |

The table is read from `staging/timetracking/` with Auto Loader, written with `append`, and tracked by the `bronze_timetracking` checkpoint.

### `bronze_documents_manifest`

**Grain:** One row per JSON document or invoice manifest.

| Column | Type | Description |
|---|---|---|
| `document_id` | Inferred from JSON | Document or invoice identifier. |
| `expense_id` | Inferred from JSON, nullable | Expense identifier for vendor invoices. |
| `project_id` | Inferred from JSON, nullable | Related project identifier. |
| `task_id` | Inferred from JSON, nullable | Related task identifier. |
| `document_category` | Inferred from JSON | Document category, including `vendor_invoice`. |
| `vendor_name` | Inferred from JSON, nullable | Vendor name for invoices. |
| `category` | Inferred from JSON, nullable | Expense category for invoices. |
| `expense_date` | Inferred from JSON, nullable | Invoice expense date. |
| `amount` | Inferred from JSON, nullable | Invoice amount. |
| `currency` | Inferred from JSON, nullable | Invoice currency. |
| `file_name` | Inferred from JSON | Physical file name. |
| `file_extension` | Inferred from JSON | File extension. |
| `file_size_bytes` | Inferred from JSON | File size in bytes. |
| `sha256_checksum` | Inferred from JSON | File checksum. |
| `created_at` | Inferred from JSON | Source creation timestamp. |
| `tags` | Inferred from JSON | Source tags array. |
| `_ingested_at` | TIMESTAMP | Auto Loader ingestion timestamp. |
| `_source_file` | STRING | Input manifest path from `_metadata.file_path`. |
| `adls_raw_uri` | STRING | `_source_file` with the `.json` suffix removed. |

The table is read from `staging/documents_raw/` with Auto Loader, filtered to `*.json`, written with `append`, and tracked by the `bronze_docs` checkpoint.

## 2. Silver layer

Silver transformations trim and cast source fields, remove duplicate natural identifiers, validate rows, and write invalid-row summaries to `quarantine_master`.

### `silver_users`

**Grain:** One validated row per user.

| Column | Type | Description |
|---|---|---|
| `user_id` | INT | Natural user identifier. |
| `full_name` | STRING | Trimmed and title-cased name. |
| `email` | STRING | Trimmed and lowercased email. |
| `department` | STRING | Trimmed department. |
| `role` | STRING | Trimmed role. |
| `hourly_rate` | DOUBLE | Source rate or default `75.0` when the source column is absent. |
| `is_active` | BOOLEAN | Active-user flag. |
| `_transformed_at` | TIMESTAMP | Silver transformation timestamp. |

Rows are valid when `user_id` is present, the email contains `@`, and `hourly_rate` is greater than zero.

### `silver_projects`

**Grain:** One validated row per project.

| Column | Type | Description |
|---|---|---|
| `project_id` | STRING | Trimmed natural project identifier. |
| `project_name` | STRING | Trimmed project name. |
| `status` | STRING | Project status as supplied by the source. |
| `start_date` | DATE | Parsed project start date. |
| `due_date` | DATE | Parsed project due date. |
| `budget_hours` | DOUBLE | Numeric labor-hour budget. |
| `budget_amount` | DOUBLE | Numeric budget, or `budget_hours * 75.0` when the source column is absent. |
| `_transformed_at` | TIMESTAMP | Silver transformation timestamp. |

Rows are valid when `project_id` is present, `start_date <= due_date`, and both budget values are non-negative.

### `silver_tasks`

**Grain:** One validated row per task.

| Column | Type | Description |
|---|---|---|
| `task_id` | STRING | Trimmed natural task identifier. |
| `project_id` | STRING | Trimmed parent project identifier. |
| `assigned_user_id` | INT | Assigned user identifier, nullable. |
| `task_name` | STRING | Trimmed task name. |
| `priority` | STRING | Trimmed task priority. |
| `status` | STRING | Trimmed task status. |
| `estimated_hours` | INT | Cast estimated effort. |
| `_transformed_at` | TIMESTAMP | Silver transformation timestamp. |

Valid statuses are `To Do`, `In Progress`, `Done`, and `Blocked`. Rows are valid when `task_id` and `project_id` are present and `estimated_hours > 0`.

### `silver_timetracking`

**Grain:** One validated row per exploded time-tracking log entry.

| Column | Type | Description |
|---|---|---|
| `entry_id` | STRING | Trimmed time-entry identifier. |
| `project_id` | STRING | Trimmed project identifier. |
| `task_id` | STRING | Trimmed task identifier. |
| `user_id` | INT | User identifier. |
| `work_date` | DATE | Parsed source log date. |
| `hours_worked` | DOUBLE | Logged hours; must be greater than 0 and at most 24. |
| `progress_pct` | DOUBLE | Progress percentage; null values become `0.0`. |
| `activity_description` | STRING | Trimmed activity description. |
| `_source_file` | STRING | Original Bronze source path. |
| `_transformed_at` | TIMESTAMP | Silver transformation timestamp. |

`is_billable` is parsed in the declared nested schema but is not selected into `silver_timetracking`. Valid rows require an entry ID, non-empty task ID, valid hours, a non-future work date, and progress between 0 and 100.

### `silver_documents`

**Grain:** One validated non-invoice document manifest.

| Column | Type | Description |
|---|---|---|
| `document_id` | STRING | Trimmed document identifier. |
| `project_id` | STRING | Trimmed project identifier. |
| `task_id` | STRING | Trimmed task identifier. |
| `document_category` | STRING | Document category excluding `vendor_invoice`. |
| `file_name` | STRING | Trimmed file name. |
| `file_type` | STRING | Uppercase file extension. |
| `file_size_mb` | DOUBLE | File size converted from bytes to megabytes. |
| `adls_raw_uri` | STRING | Raw ADLS URI derived from the source manifest path. |
| `_transformed_at` | TIMESTAMP | Silver transformation timestamp. |

Valid rows require a document ID, a non-empty project ID, and a positive file size.

### `silver_expenses`

**Grain:** One validated vendor invoice.

| Column | Type | Description |
|---|---|---|
| `expense_id` | STRING | Trimmed expense identifier. |
| `project_id` | STRING | Trimmed project identifier. |
| `expense_date` | DATE | Parsed invoice date. |
| `category` | STRING | Expense category. |
| `vendor_name` | STRING | Trimmed and title-cased vendor name. |
| `amount` | DOUBLE | Invoice amount. |
| `adls_raw_uri` | STRING | Raw ADLS URI derived from the source manifest path. |
| `_transformed_at` | TIMESTAMP | Silver transformation timestamp. |

Valid rows require an expense ID, a project ID, and a positive amount.

### `quarantine_master`

**Grain:** One summary row per rejected source record and entity processing run.

| Column | Type | Description |
|---|---|---|
| `source_table` | STRING | Source Bronze table name, such as `bronze_tasks`. |
| `record_id` | STRING | Rejected natural identifier, or `UNKNOWN` when null. |
| `issue_reason` | STRING | Semicolon-delimited validation failure reason. |
| `quarantined_at` | TIMESTAMP | Quarantine timestamp. |

The helper removes duplicate IDs before validation, writes valid Silver data with `overwrite`, and writes quarantine data using `overwrite` with a `replaceWhere` predicate for the current source table.

## 3. Gold dimensions

Gold dimensions are rebuilt with `MERGE INTO` and `overwriteSchema=true`.

### `dim_user`

**Grain:** One row per Silver user. **Key:** `user_key = MD5(CAST(user_id AS STRING))`.

| Column | Type | Description |
|---|---|---|
| `user_key` | STRING | Deterministic MD5 surrogate key. |
| `user_id` | INT | Natural user identifier. |
| `full_name` | STRING | User name retained from Silver. |
| `email` | STRING | User email. |
| `department` | STRING | User department. |
| `role` | STRING | User role. |
| `hourly_rate` | DOUBLE | Rate card selected from role-based rules. |
| `is_active` | BOOLEAN | Active-user flag. |
| `_loaded_at` | TIMESTAMP | Gold load timestamp. |

### `dim_project`

**Grain:** One row per Silver project. **Key:** `project_key = MD5(CAST(project_id AS STRING))`.

| Column | Type | Description |
|---|---|---|
| `project_key` | STRING | Deterministic MD5 surrogate key. |
| `project_id` | STRING | Natural project identifier. |
| `project_name` | STRING | Project name. |
| `status` | STRING | Project status. |
| `start_date` | DATE | Project start date. |
| `due_date` | DATE | Project due date. |
| `budget_hours` | DOUBLE | Planned labor-hour budget. |
| `budget_amount` | DOUBLE | Budget, falling back to `budget_hours * 75.0` when null. |
| `_loaded_at` | TIMESTAMP | Gold load timestamp. |

### `dim_task`

**Grain:** One row per Silver task. **Key:** `task_key = MD5(CAST(task_id AS STRING))`.

| Column | Type | Description |
|---|---|---|
| `task_key` | STRING | Deterministic MD5 surrogate key. |
| `task_id` | STRING | Natural task identifier. |
| `project_id` | STRING | Natural parent project identifier. |
| `assigned_user_id` | INT | Assigned user identifier. |
| `task_name` | STRING | Task name. |
| `priority` | STRING | Task priority. |
| `status` | STRING | Task status. |
| `estimated_hours` | INT | Current estimated effort. |
| `_loaded_at` | TIMESTAMP | Gold load timestamp. |

### `dim_date`

**Grain:** One row per calendar day from `2026-01-01` through `2026-12-31`.

| Column | Type | Description |
|---|---|---|
| `date_key` | INT | Date formatted as `YYYYMMDD`. |
| `calendar_date` | DATE | Calendar date. |
| `year` | INT | Calendar year. |
| `quarter` | INT | Calendar quarter. |
| `month` | INT | Calendar month number. |
| `month_name` | STRING | Full month name. |
| `day_of_month` | INT | Day number within the month. |
| `day_name` | STRING | Full weekday name. |
| `is_weekend` | BOOLEAN | True for Saturday or Sunday. |

## 4. Gold fact tables

All three fact tables are currently written with `overwrite`, not `append`.

### `fact_timesheet`

**Grain:** One row per validated time-entry event.

| Column | Type | Description |
|---|---|---|
| `entry_id` | STRING | Natural time-entry identifier. |
| `user_key` | STRING | User surrogate key or `"-1"`. |
| `project_key` | STRING | Project surrogate key or `"-1"`. |
| `task_key` | STRING | Task surrogate key or `"-1"`. |
| `date_key` | INT | Work date in `YYYYMMDD` format. |
| `hours_worked` | DOUBLE | Logged hours. |
| `labor_cost` | DOUBLE | Hours multiplied by the matched hourly rate, defaulting to `70.0`. |
| `progress_pct` | DOUBLE | Reported progress percentage. |
| `activity_description` | STRING | Work description. |
| `_loaded_at` | TIMESTAMP | Gold load timestamp. |

### `fact_expenses`

**Grain:** One row per validated vendor invoice.

| Column | Type | Description |
|---|---|---|
| `expense_id` | STRING | Natural expense identifier. |
| `project_key` | STRING | Project surrogate key or `"-1"`. |
| `date_key` | INT | Expense date in `YYYYMMDD` format; may be null if the source date is null. |
| `category` | STRING | Expense category. |
| `vendor_name` | STRING | Vendor name. |
| `expense_amount` | DOUBLE | Invoice amount. |
| `adls_raw_uri` | STRING | Link to the raw ADLS asset. |
| `_loaded_at` | TIMESTAMP | Gold load timestamp. |

### `fact_project_documents`

**Grain:** One row per validated non-invoice project document.

| Column | Type | Description |
|---|---|---|
| `document_id` | STRING | Natural document identifier. |
| `project_key` | STRING | Project surrogate key or `"-1"`. |
| `task_key` | STRING | Task surrogate key or `"-1"`. |
| `file_name` | STRING | Document file name. |
| `file_type` | STRING | Uppercase file extension. |
| `file_size_mb` | DOUBLE | Document size in megabytes. |
| `document_count` | INT | Constant value of `1`. |
| `_loaded_at` | TIMESTAMP | Gold load timestamp. |

## 5. Gold current-state marts

### `agg_task_overview`

**Grain:** One row per task.

| Column | Type | Description |
|---|---|---|
| `task_key` | STRING | Task surrogate key. |
| `task_id` | STRING | Natural task identifier. |
| `task_name` | STRING | Task name. |
| `project_id` | STRING | Parent project identifier. |
| `project_name` | STRING | Parent project name. |
| `assignee_name` | STRING | Assigned user's full name. |
| `assignee_department` | STRING | Assigned user's department. |
| `priority` | STRING | Task priority. |
| `task_status` | STRING | Current task status. |
| `estimated_hours` | INT | Current estimated effort. |
| `actual_hours_logged` | DOUBLE | Sum of logged hours for the task, defaulting to zero. |
| `latest_progress_pct` | DOUBLE | Maximum recorded progress percentage, defaulting to zero. |
| `hour_variance` | DOUBLE | Actual hours minus estimated hours; positive means overrun. |
| `hours_per_progress_pct` | DOUBLE | Actual hours divided by progress percentage, using `1` as the zero-progress denominator. |
| `total_labor_cost` | DOUBLE | Total labor cost for the task. |
| `total_work_sessions` | BIGINT | Number of time-entry rows for the task. |
| `execution_health` | STRING | `Completed`, `Blocked / Impeded`, `Effort Overrun`, `Stalled Progress`, or `On Track`. |
| `_updated_at` | TIMESTAMP | Mart refresh timestamp. |

### `agg_project_overview`

**Grain:** One row per project.

| Column | Type | Description |
|---|---|---|
| `project_key` | STRING | Project surrogate key. |
| `project_id` | STRING | Natural project identifier. |
| `project_name` | STRING | Project name. |
| `status` | STRING | Project status. |
| `budget_hours` | DOUBLE | Planned labor-hour budget. |
| `actual_hours` | DOUBLE | Total timesheet hours. |
| `hours_variance` | DOUBLE | Budget hours minus actual hours. |
| `hours_burn_rate_pct` | DOUBLE | Actual hours divided by budget hours times 100. |
| `budget_amount` | DOUBLE | Planned monetary budget. |
| `labor_cost` | DOUBLE | Total labor cost. |
| `non_labor_cost` | DOUBLE | Total expense cost. |
| `total_actual_cost` | DOUBLE | Labor cost plus non-labor cost. |
| `financial_variance` | DOUBLE | Budget amount minus actual cost. |
| `cost_burn_rate_pct` | DOUBLE | Actual cost divided by budget amount times 100. |
| `total_tasks` | BIGINT | Number of project tasks. |
| `completed_tasks` | BIGINT | Number of tasks with status `Done`. |
| `task_completion_pct` | DOUBLE | Completed tasks divided by total tasks times 100. |
| `total_documents` | BIGINT | Number of project documents. |
| `total_storage_mb` | DOUBLE | Total project document storage. |
| `avg_task_progress_pct` | DOUBLE | Average task progress. |
| `blocked_tasks` | BIGINT | Number of tasks with status `Blocked`. |
| `_updated_at` | TIMESTAMP | Mart refresh timestamp. |

## 6. Historical snapshot facts

Both snapshot tables use `append`, are partitioned by `snapshot_date`, and receive the current-state mart rows with `F.current_date()`.

### `fact_project_snapshot`

**Grain:** One project overview row per snapshot date.

Columns are all columns from `agg_project_overview` plus:

| Column | Type | Description |
|---|---|---|
| `snapshot_date` | DATE | Date on which the project overview was captured; partition column. |

### `fact_task_snapshot`

**Grain:** One task overview row per snapshot date.

Columns are all columns from `agg_task_overview` plus:

| Column | Type | Description |
|---|---|---|
| `snapshot_date` | DATE | Date on which the task overview was captured; partition column. |

The notebook does not deduplicate by task/project and `snapshot_date`, so rerunning the snapshot cells for the same date can append duplicate observations.

## 7. Implementation caveats

These items describe behavior present in the notebooks and should not be interpreted as additional implemented features:

1. The time-tracking source JSON contains `logs` as an array of structs. The Silver notebook currently calls `from_json()` on `logs`, which expects a string and may require correction before execution.
2. The `is_billable` field is parsed from time-tracking input but is not retained in Silver or Gold.
3. The `"-1"` unknown foreign-key value is used in facts, but the notebooks do not insert explicit unknown rows into the dimensions.
4. `hours_burn_rate_pct` and `cost_burn_rate_pct` do not guard against zero budgets.
5. The date dimension is fixed to calendar year 2026 rather than being dynamically generated from source dates.
6. The current quarantine table stores rejection summaries rather than complete rejected records.
