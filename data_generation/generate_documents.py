import pandas as pd
import os
import json
import random
import uuid
import hashlib
from datetime import datetime, timedelta

# set seed for deterministic data 
random.seed(42)

out_folder = "./data/source_systems/company_server"
os.makedirs(out_folder, exist_ok=True)

# load the tasks generated earlier 
tasks_df = pd.read_csv("./data/source_systems/rdbms/tasks.csv")
project_list = tasks_df["project_id"].dropna().unique().tolist()

#  timestamp for databricks autoloader to see new files on each run
run_time = datetime.now().strftime("%Y%m%d_%H%M%S")

# pick 15 random tasks to generate fake files for
sample_tasks = tasks_df.sample(15, random_state=42)

# simple list of file types to pick from
file_types = [
    ("architecture_doc", "pdf", b"%PDF-1.4 mock pdf..."),
    ("wireframe", "png", b"\x89PNG\r\n mock png..."),
    ("code_backup", "zip", b"PK\x03\x04 mock zip...")
]

for index, row in sample_tasks.iterrows():
    p_id = str(row["project_id"])
    t_id = str(row["task_id"])
    
    # pick a random file type from the list above
    f_type = random.choice(file_types)
    doc_type = f_type[0]
    ext = f_type[1]
    raw_bytes = f_type[2]
    
    fname = f"{p_id}_{t_id}_{doc_type}.{ext}"
    
    # add some dummy bytes to make the file size more realistic
    dummy_data = raw_bytes + (b"0" * random.randint(1000, 50000))
    
    with open(f"{out_folder}/{fname}", "wb") as f:
        f.write(dummy_data)
        
    # create the json manifest for this file
    meta = {
        "document_id": f"DOC-{uuid.uuid4().hex[:8].upper()}",
        "project_id": p_id,
        "task_id": t_id,
        "document_category": doc_type,
        "file_name": fname,
        "file_extension": ext,
        "file_size_bytes": len(dummy_data),
        "sha256_checksum": hashlib.sha256(dummy_data).hexdigest(),
        "created_at": str(datetime.now()),
        "tags": [ext]
    }
    
    # save json with the timestamp so older runs don't overwrite newer runs
    json_name = f"{fname}_{run_time}.json"
    with open(f"{out_folder}/{json_name}", "w") as f:
        json.dump(meta, f, indent=2)


# generate vendor invoices (1 or 2 per project)
vendors = [
    ("Azure", "Cloud", 500, 1500),
    ("AWS", "Cloud", 400, 1200),
    ("Figma", "Design", 100, 300)
]

inv_count = 3001

for pid in project_list:
    num_inv = random.randint(1, 2)
    
    for i in range(num_inv):
        v_choice = random.choice(vendors)
        v_name = v_choice[0]
        v_cat = v_choice[1]
        amt = round(random.uniform(v_choice[2], v_choice[3]), 2)
        
        inv_num = f"INV-{inv_count}"
        
        # random date in the past
        days_ago = random.randint(10, 60)
        inv_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        pdf_bytes = f"%PDF-1.4 Invoice {inv_num}".encode("utf-8") + (b"0" * random.randint(1000, 5000))
        pdf_name = f"{pid}_{inv_num}_{v_name}.pdf"
        
        with open(f"{out_folder}/{pdf_name}", "wb") as f:
            f.write(pdf_bytes)
            
        #  insert bad data for testing the databricks quarantine table
        if inv_count == 3005:
            amt = -500.0   # bad amount
            final_pid = "" # missing project id link
        else:
            final_pid = pid
            
        inv_meta = {
            "document_id": inv_num,
            "expense_id": f"EXP-{inv_count}",
            "project_id": final_pid,
            "task_id": None,
            "document_category": "vendor_invoice",
            "vendor_name": v_name,
            "category": v_cat,
            "expense_date": inv_date,
            "amount": amt,
            "currency": "EUR",
            "file_name": pdf_name,
            "file_extension": "pdf",
            "file_size_bytes": len(pdf_bytes),
            "sha256_checksum": hashlib.sha256(pdf_bytes).hexdigest(),
            "created_at": str(datetime.now()),
            "tags": ["INVOICE"]
        }
        
        json_name = f"{pdf_name}_{run_time}.json"
        with open(f"{out_folder}/{json_name}", "w") as f:
            json.dump(inv_meta, f, indent=2)
            
        inv_count += 1

print("Done making files!")