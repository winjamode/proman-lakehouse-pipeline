SELECT 
    u.full_name,
    DATE_TRUNC('week', d.calendar_date) AS work_week,
    ROUND(SUM(f.hours_worked), 1) AS weekly_hours
FROM dbw_proman_lakehouse_01.default.fact_timesheet f
JOIN dbw_proman_lakehouse_01.default.dim_user u ON f.user_key = u.user_key
JOIN dbw_proman_lakehouse_01.default.dim_date d ON f.date_key = d.date_key
WHERE f.user_key != "-1"
GROUP BY u.full_name, DATE_TRUNC('week', d.calendar_date)
ORDER BY work_week;