SELECT 
    assignee_name AS full_name,
    project_name,
    task_id,
    task_name,
    priority,
    task_status,
    estimated_hours,
    actual_hours_logged,
    latest_progress_pct,
    hour_variance,
    execution_health
FROM dbw_proman_lakehouse_01.default.agg_task_overview
ORDER BY actual_hours_logged DESC;