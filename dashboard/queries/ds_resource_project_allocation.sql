WITH user_effort AS (
    SELECT 
        u.full_name,
        p.project_name,
        p.status AS project_status,
        ROUND(SUM(f.hours_worked), 1) AS hours_on_project,
        ROUND(SUM(f.labor_cost), 2) AS cost_on_project
    FROM dbw_proman_lakehouse_01.default.fact_timesheet f
    JOIN dbw_proman_lakehouse_01.default.dim_user u ON f.user_key = u.user_key
    JOIN dbw_proman_lakehouse_01.default.dim_project p ON f.project_key = p.project_key
    WHERE f.user_key != "-1" AND f.project_key != "-1"
    GROUP BY u.full_name, p.project_name, p.status
)
SELECT 
    full_name,
    project_name,
    project_status,
    hours_on_project,
    cost_on_project,
    ROUND(
        (hours_on_project / SUM(hours_on_project) OVER (PARTITION BY full_name)) * 100, 1
    ) AS allocation_share_pct
FROM user_effort
ORDER BY hours_on_project DESC;