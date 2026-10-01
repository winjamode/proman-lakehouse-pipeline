WITH weekly_burn AS (
    SELECT 
        p.project_name,
        d.year,
        DATE_TRUNC('week', d.calendar_date) AS work_week,
        ROUND(SUM(f.hours_worked), 1) AS weekly_hours,
        ROUND(SUM(f.labor_cost), 2) AS weekly_labor_spend
    FROM dbw_proman_lakehouse_01.default.fact_timesheet f
    JOIN dbw_proman_lakehouse_01.default.dim_date d ON f.date_key = d.date_key
    JOIN dbw_proman_lakehouse_01.default.dim_project p ON f.project_key = p.project_key
    WHERE f.project_key != "-1"
    GROUP BY p.project_name, d.year, DATE_TRUNC('week', d.calendar_date)
)
SELECT 
    project_name,
    work_week,
    weekly_hours,
    weekly_labor_spend,
    ROUND(
        SUM(weekly_labor_spend) OVER (
            PARTITION BY project_name 
            ORDER BY work_week 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 2
    ) AS cumulative_labor_spend
FROM weekly_burn
ORDER BY project_name, work_week;