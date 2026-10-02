import os
import json
import random
from datetime import datetime, timedelta
import pandas as pd

random.seed(42) # set seed for deterministic data 

out_folder = "./data/source_systems/timetracking"
os.makedirs(out_folder, exist_ok=True)

tasks_df = pd.read_csv("./data/source_systems/rdbms/tasks.csv")

# simple list of activities to randomly pick from
activities = [
    "Created the database schema",
    "Fixed the CI/CD pipeline",
    "Fixed CSS bugs",
    "Added unit tests",
    "Made the SQL queries faster",
    "Refactored login stuff",
    "Sprint planning meeting",
    "Code review with the team",
    "Updated the documentation",
    "Debugging environment issues"
]

logs = []
log_id = 1001
today = datetime.now()

for index, row in tasks_df.iterrows():
    status = str(row["status"])
    est_hrs = float(row["estimated_hours"])

    if status == "To Do":
        continue # hasn't started yet
        
    # Backward compatibility: Determine how much is done based on the task status
    if status == "Done":
        final_prog = 100
        total_hrs = est_hrs * random.uniform(0.9, 1.1) # roughly on budget
    elif status == "Blocked":
        final_prog = random.randint(30, 45)
        total_hrs = est_hrs * random.uniform(1.2, 1.4) # over budget
    else:
        # in progress
        final_prog = random.randint(45, 75)
        total_hrs = est_hrs * (final_prog / 100.0)

    # split the work across 3 to 5 separate days
    num_days = random.randint(3, 5)
    
    # divide the hours up randomly
    splits = [random.uniform(1, 3) for _ in range(num_days)]
    total_split = sum(splits)
    
    session_hrs = []
    for s in splits:
        session_hrs.append(round((s / total_split) * total_hrs, 1))
        
    # make sure the last session is adjusted so the total hours matches exactly
    session_hrs[-1] = round(session_hrs[-1] + (total_hrs - sum(session_hrs)), 1)

    # randomly picking days in the past for the work sessions
    days_ago = sorted([random.randint(3, 45) for _ in range(num_days)], reverse=True)

    for i in range(num_days):
        # fake the progress percentage increasing over time
        if i == num_days - 1:
            prog_val = final_prog
        else:
            prog_val = max(5, int(final_prog * ((i + 1) / num_days)))
            # make sure the progress is always increasing
        work_date = today - timedelta(days=days_ago[i])

        logs.append({
            "entry_id": f"LOG-{log_id}",
            "project_id": str(row["project_id"]),
            "task_id": str(row["task_id"]),
            "user_id": int(row["assigned_user_id"]),
            "date": work_date.strftime("%Y-%m-%d"),
            "hours_worked": max(0.5, session_hrs[i]),
            "progress_pct": prog_val,
            "activity_description": random.choice(activities),
            "is_billable": True
        })
        log_id += 1

# introducing bad record for testing the databricks quarantine table
logs.append({
    "entry_id": "LOG-9999",
    "project_id": "PRJ-2001",
    "task_id": "TSK-5001",
    "user_id": 101,
    "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"), # future date
    "hours_worked": 26.5, # over 24 hours in a day
    "progress_pct": 150,  # can't be over 100
    "activity_description": "Testing quarantine bad data",
    "is_billable": True
})

# building the final json payload
out_data = {
    "system_name": "ProMan-TimeSync-Microservice",
    "export_version": "3.2.0",
    "extracted_at": str(today),
    "record_count": len(logs),
    "logs": logs
}

# timestamp the file so databricks autoloader sees it as a new file each time
run_time = datetime.now().strftime("%Y%m%d_%H%M%S")
file_name = f"time_tracking_{run_time}.json"
file_path = os.path.join(out_folder, file_name)

with open(file_path, "w") as f:
    json.dump(out_data, f, indent=2)

print(f"done! saved {len(logs)} logs to {file_path}")