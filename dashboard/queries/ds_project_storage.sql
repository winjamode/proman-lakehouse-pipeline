SELECT 
    p.project_name,
    d.file_type,
    COUNT(d.document_id) AS file_count,
    ROUND(SUM(d.file_size_mb), 2) AS storage_mb
FROM dbw_proman_lakehouse_01.default.fact_project_documents d
JOIN dbw_proman_lakehouse_01.default.dim_project p ON d.project_key = p.project_key
WHERE d.project_key != "-1"
GROUP BY p.project_name, d.file_type
ORDER BY storage_mb DESC;