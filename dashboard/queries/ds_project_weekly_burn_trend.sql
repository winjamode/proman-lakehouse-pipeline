WITH weekly_labor AS (
    SELECT 
        f.project_key,
        DATE_TRUNC('week', d.calendar_date) AS work_week,
        SUM(f.hours_worked) AS weekly_hours,
        SUM(f.labor_cost) AS weekly_labor
    FROM dbw_proman_lakehouse_01.default.fact_timesheet f
    JOIN dbw_proman_lakehouse_01.default.dim_date d ON f.date_key = d.date_key
    WHERE f.project_key != "-1"
    GROUP BY f.project_key, DATE_TRUNC('week', d.calendar_date)
),

weekly_expenses AS (
    SELECT 
        e.project_key,
        DATE_TRUNC('week', d.calendar_date) AS work_week,
        SUM(e.expense_amount) AS weekly_expenses
    FROM dbw_proman_lakehouse_01.default.fact_expenses e
    JOIN dbw_proman_lakehouse_01.default.dim_date d ON e.date_key = d.date_key
    WHERE e.project_key != "-1"
    GROUP BY e.project_key, DATE_TRUNC('week', d.calendar_date)
),

weekly_joined AS (
    SELECT 
        COALESCE(l.project_key, x.project_key) AS project_key,
        COALESCE(l.work_week, x.work_week) AS work_week,
        COALESCE(l.weekly_labor, 0) AS weekly_labor,
        COALESCE(x.weekly_expenses, 0) AS weekly_expenses
    FROM weekly_labor l
    FULL OUTER JOIN weekly_expenses x 
        ON l.project_key = x.project_key AND l.work_week = x.work_week
)

SELECT 
    p.project_name,
    j.work_week,
    -- 1. Cumulative Labor Line
    ROUND(
        SUM(j.weekly_labor) OVER (
            PARTITION BY p.project_name 
            ORDER BY j.work_week 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 2
    ) AS cumulative_labor_spend,
    -- 2. Cumulative Expenses Line
    ROUND(
        SUM(j.weekly_expenses) OVER (
            PARTITION BY p.project_name 
            ORDER BY j.work_week 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 2
    ) AS cumulative_expense_spend,
    -- 3. Cumulative Total Spend Line
    ROUND(
        SUM(j.weekly_labor + j.weekly_expenses) OVER (
            PARTITION BY p.project_name 
            ORDER BY j.work_week 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 2
    ) AS cumulative_total_spend
FROM weekly_joined j
JOIN dbw_proman_lakehouse_01.default.dim_project p 
    ON j.project_key = p.project_key
ORDER BY project_name, work_week;