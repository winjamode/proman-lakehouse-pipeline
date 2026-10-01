import os
import glob
import json
import random
from datetime import datetime

out_folder = "./data/source_systems/timetracking"

# 1. Grab every single log from all existing JSON files
all_logs = []
for file_path in glob.glob(os.path.join(out_folder, "*.json")):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        all_logs.extend(data.get("logs", []))

# 2. Filter out the quarantine record and sort descending by the integer ID
valid_logs = [
    log for log in all_logs 
    if log["entry_id"].startswith("LOG-")
    and log["entry_id"] != "LOG-9999"
    and log["project_id"] != "PRJ-9999"
    and log["task_id"] != "TSK-9999"
]
valid_logs.sort(key=lambda x: int(x["entry_id"].split("-")[1]), reverse=True)

# 3. Pick the single latest log for unique tasks (e.g., top 5 distinct tasks)
unique_task_logs = []
seen_tasks = set()

for log in valid_logs:
    t_id = log["task_id"]
    if t_id not in seen_tasks:
        seen_tasks.add(t_id)
        unique_task_logs.append(log)
        if len(unique_task_logs) == 5:  # change to 10 if you want 10 tasks
            break

if not unique_task_logs:
    print("No valid logs found to generate incremental updates.")
    exit()

# Set up new starting ID based on the highest existing log ID
next_id = int(valid_logs[0]["entry_id"].split("-")[1]) + 1
today_str = datetime.now().strftime("%Y-%m-%d")

# 4. Generate exactly 1 new incremental log per task
new_logs = []
for old_log in unique_task_logs:
    # If the task was already finished at 100%, keep it at 100%
    if old_log["progress_pct"] >= 100:
        new_prog = 100
    else:
        new_prog = min(100, old_log["progress_pct"] + random.randint(5, 15))
    
    new_logs.append({
        "entry_id": f"LOG-{next_id}",
        "project_id": old_log["project_id"],
        "task_id": old_log["task_id"],
        "user_id": old_log["user_id"],
        "date": today_str,
        "hours_worked": round(random.uniform(1.0, 4.0), 1),
        "progress_pct": new_prog,
        "activity_description": "Day 2 continuation of work",
        "is_billable": True
    })
    next_id += 1

# 5. Save the new delta JSON
out_data = {
    "system_name": "ProMan-TimeSync-Microservice",
    "export_version": "3.2.0",
    "extracted_at": str(datetime.now()),
    "record_count": len(new_logs),
    "logs": new_logs
}

run_time = datetime.now().strftime("%Y%m%d_%H%M%S")
file_path = os.path.join(out_folder, f"time_tracking_{run_time}.json")

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(out_data, f, indent=2)

print(f" Generated {len(new_logs)} incremental logs in {file_path}")