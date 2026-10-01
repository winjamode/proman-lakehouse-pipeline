SELECT 
    u.user_id,
    u.full_name,
    u.department,
    u.role,
    u.hourly_rate,
    u.is_active,
    COUNT(DISTINCT f.date_key) AS active_working_days,
    ROUND(COALESCE(SUM(f.hours_worked), 0.0), 1) AS total_logged_hours,
    ROUND(COALESCE(SUM(f.labor_cost), 0.0), 2) AS total_cost_generated,
    ROUND(
        COALESCE(SUM(f.hours_worked), 0.0) / NULLIF(COUNT(DISTINCT f.date_key), 0), 2
    ) AS avg_daily_hours,
    COUNT(DISTINCT f.project_key) AS total_assigned_projects
FROM dbw_proman_lakehouse_01.default.dim_user u
LEFT JOIN dbw_proman_lakehouse_01.default.fact_timesheet f ON u.user_key = f.user_key
WHERE u.user_key != "-1"
GROUP BY u.user_id, u.full_name, u.department, u.role, u.hourly_rate, u.is_active;