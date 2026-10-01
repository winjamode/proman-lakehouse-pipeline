SELECT 
    project_name,
    task_id,
    task_name,
    assignee_name,
    assignee_department,
    priority,
    task_status,
    estimated_hours,
    actual_hours_logged,
    latest_progress_pct,
    hour_variance,
    hours_per_progress_pct,
    execution_health
FROM dbw_proman_lakehouse_01.default.agg_task_overview
ORDER BY actual_hours_logged DESC;