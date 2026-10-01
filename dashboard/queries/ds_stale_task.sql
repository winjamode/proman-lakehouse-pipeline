WITH RankedSnapshots AS (
    SELECT 
        task_id,
        task_name,
        assignee_name,
        project_name,
        task_status,
        actual_hours_logged,
        snapshot_date,
        -- Rank snapshots backwards from today (1 = most recent)
        DENSE_RANK() OVER (ORDER BY snapshot_date DESC) as snap_rank
    FROM dbw_proman_lakehouse_01.default.fact_task_snapshot
    WHERE task_status IN ('In Progress', 'Blocked')
)
SELECT 
    task_id,
    task_name,
    assignee_name,
    project_name,
    task_status AS current_status,
    MAX(actual_hours_logged) AS stalled_hours,
    MIN(snapshot_date) AS stalled_since_date
FROM RankedSnapshots
WHERE snap_rank <= 2 --  2 most recent snapshots
GROUP BY task_id, task_name, assignee_name, project_name, task_status
-- Only keep tasks where the maximum hours logged equals the minimum hours logged 
-- (meaning 0 hours were added over the last 2 snapshots)
HAVING MAX(actual_hours_logged) = MIN(actual_hours_logged)
   -- Ensure the task actually existed in all 2 snapshots
   AND COUNT(DISTINCT snap_rank) >= 2
ORDER BY stalled_since_date ASC