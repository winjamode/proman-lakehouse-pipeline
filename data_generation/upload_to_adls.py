import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()


STORAGE_ACCOUNT = "adlspromandev01"
CONTAINER_NAME = "datalake"
CONNECTION_STRING = os.getenv("CONNECTION_STRING")

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

files_to_upload = [
    (
        "./data/source_systems/rdbms/customers.csv",
        "staging/rdbms/customers.csv",
    ),
    (
        "./data/source_systems/rdbms/orders.csv",
        "staging/rdbms/orders.csv",
    ),
    (
        "./data/source_systems/timetracking/time_entries.csv",
        "staging/timetracking/time_entries.csv",
    ),
    (
        "./data/source_systems/company_server/company_document.pdf",
        "staging/documents_raw/company_document.pdf",
    ),
]

print("Starting extraction and loading into ADLS Gen2 Staging layer...")

for local_path, blob_path in files_to_upload:
    if not os.path.isfile(local_path):
        print(f"  [Skipped] File not found: {local_path}")
        continue

    blob_client = container_client.get_blob_client(blob_path)

    with open(local_path, "rb") as file_data:
        blob_client.upload_blob(file_data, overwrite=True)

    print(f"  [Loaded] {local_path} -> {blob_path}")

print("Raw data loading phase complete. All files have been uploaded to ADLS Gen2.")

