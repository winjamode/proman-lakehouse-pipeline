SELECT 
    p.project_name,
    e.expense_id,
    e.category,
    e.vendor_name,
    d.calendar_date AS invoice_date,
    e.expense_amount,
    e.adls_raw_uri
FROM dbw_proman_lakehouse_01.default.fact_expenses e
JOIN dbw_proman_lakehouse_01.default.dim_project p ON e.project_key = p.project_key
JOIN dbw_proman_lakehouse_01.default.dim_date d ON e.date_key = d.date_key
WHERE e.project_key != "-1"
ORDER BY invoice_date DESC;