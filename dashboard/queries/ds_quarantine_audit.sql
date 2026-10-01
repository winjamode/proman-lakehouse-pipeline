SELECT 
    source_table,
    issue_reason,
    COUNT(*) AS rejected_records_count,
    MAX(quarantined_at) AS last_occurrence
FROM dbw_proman_lakehouse_01.default.quarantine_master
GROUP BY source_table, issue_reason
ORDER BY rejected_records_count DESC;