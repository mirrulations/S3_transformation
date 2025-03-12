import boto3
import re
import time
from concurrent.futures import ThreadPoolExecutor

s3 = boto3.client('s3')

BUCKET_NAME = "s3fakecs334s25"
SOURCE_PREFIX = ""
RAW_DATA_PREFIX = "Raw_data/"
DERIVED_DATA_PREFIX = "Derived_data/"

def create_placeholder(bucket_name, key):
    """Creates a placeholder file in the specified folder."""
    try:
        s3.put_object(Bucket=bucket_name, Key=key, Body="This is a placeholder file.")
        print(f"✔ Created placeholder in folder: {key}")
    except Exception as e:
        print(f"❌ Error creating placeholder: {e}")

def create_raw_data_folder(bucket_name):
    """Ensures that Raw_data folder exists in the S3 bucket."""
    raw_data_folder = RAW_DATA_PREFIX
    try:
        s3.put_object(Bucket=bucket_name, Key=raw_data_folder)
        create_placeholder(bucket_name, raw_data_folder + "placeholder.txt")
        print(f"✔ Created Raw_data folder: {raw_data_folder}")
    except Exception as e:
        print(f"❌ Error creating Raw_data folder: {e}")

def create_derived_data_folder(bucket_name):
    """Ensures that Derived_data folder exists in the S3 bucket."""
    derived_data_folder = DERIVED_DATA_PREFIX
    try:
        s3.put_object(Bucket=bucket_name, Key=derived_data_folder)
        create_placeholder(bucket_name, derived_data_folder + "placeholder.txt")
        print(f"✔ Created Derived_data folder: {derived_data_folder}")
    except Exception as e:
        print(f"❌ Error creating Derived_data folder: {e}")

def move_object(bucket_name, source_key, dest_key):
    """Moves an object from the source to the destination in S3."""
    try:
        s3.copy_object(Bucket=bucket_name, CopySource={"Bucket": bucket_name, "Key": source_key}, Key=dest_key)
        print(f"✔ Moved: {source_key} -> {dest_key}")
        s3.delete_object(Bucket=bucket_name, Key=source_key)
        print(f"🗑 Deleted: {source_key}")
        print(f"Success moving: {source_key}")
    except Exception as e:
        print(f"❌ Error moving {source_key}: {e}")

def determine_destination(file_key):
    """Determines the destination path based on the file's structure."""
    match = re.match(r"([^/]+)/([^/]+)/(.+)", file_key)
    if not match:
        return RAW_DATA_PREFIX + file_key  # Default to Raw_data if no match

    agency, docket_id, remaining_path = match.groups()

    extracted_text_match = re.search(r"([^/]*)extracted_text", remaining_path)
    if extracted_text_match:
        extracted_text_root = extracted_text_match.group(0)  # Capture the folder containing "extracted_text"
        extracted_text_path = remaining_path.split(extracted_text_root + "/", 1)[1]  # Preserve subpath after extracted_text folder
        derived_dest = f"{DERIVED_DATA_PREFIX}{agency}/{docket_id}/Mirrulations/extracted_txt/{extracted_text_root}/{extracted_text_path}"
        return derived_dest

    # If not extracted_text, send to Raw_data
    return f"{RAW_DATA_PREFIX}{agency}/{docket_id}/{remaining_path}"

def process_file(bucket_name, file_key):
    """Processes a single file and moves it to the appropriate location."""
    if not file_key.startswith(RAW_DATA_PREFIX) and not file_key.startswith(DERIVED_DATA_PREFIX):
        dest_key = determine_destination(file_key)
        move_object(bucket_name, file_key, dest_key)

def process_files(bucket_name):
    """Processes all files in the S3 bucket using multithreading."""
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=SOURCE_PREFIX)
    
    with ThreadPoolExecutor(max_workers=64) as executor:
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    file_key = obj['Key']
                    executor.submit(process_file, bucket_name, file_key)

def main():
    print("🚀 Starting the script to move files and create folder structures.")
    
    start_time = time.time()  # Start timing
    
    # Create necessary folders once
    create_raw_data_folder(BUCKET_NAME)
    create_derived_data_folder(BUCKET_NAME)
    
    process_files(BUCKET_NAME)
    
    end_time = time.time()  # End timing
    duration = end_time - start_time  # Calculate duration
    
    print(f"✅ All tasks completed successfully in {duration:.2f} seconds.")

if __name__ == "__main__":
    main()