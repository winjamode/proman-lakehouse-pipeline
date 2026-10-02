WITH ranked AS (
    SELECT
        project_id,
        project_name,
        task_key,
        snapshot_date,
        estimated_hours,
        actual_hours_logged,
        _updated_at,
        ROW_NUMBER() OVER (
            PARTITION BY task_key, snapshot_date
            ORDER BY _updated_at DESC
        ) AS rn
    FROM dbw_proman_lakehouse_01.default.agg_task_snapshot
)

SELECT
    project_id,
    project_name,
    snapshot_date,
    SUM(estimated_hours) AS total_estimated_effort,
    SUM(actual_hours_logged) AS total_actual_hours
FROM ranked
WHERE rn = 1
GROUP BY
    project_id,
    project_name,
    snapshot_date
ORDER BY
    snapshot_date ASC;