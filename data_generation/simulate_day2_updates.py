import pandas as pd

# load the Day 1 CSV
csv_path = "./data/source_systems/rdbms/tasks.csv"
tasks_df = pd.read_csv(csv_path)


target_task = "TSK-5020" 
task_idx = tasks_df[tasks_df['task_id'] == target_task].index
if len(task_idx) > 0:
    old_hours = tasks_df.loc[task_idx[0], 'estimated_hours']
    new_hours = old_hours + 20 # adding 20 hours to the original estimate
    tasks_df.loc[task_idx[0], 'estimated_hours'] = new_hours
    print(f"Scope creep on {target_task}: estimated hours bumped from {old_hours} to {new_hours}")

# save the updated Day 2 CSV
tasks_df.to_csv(csv_path, index=False)
print("day 2 RDBMS updates saved successfully.")