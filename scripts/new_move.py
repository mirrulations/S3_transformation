import boto3
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor

s3 = boto3.client('s3')

BUCKET_NAME = "s3fakecs334s25"
SOURCE_PREFIX = ""
DEST_PREFIX = "Raw_data/"

def create_placeholder(bucket_name, key):
    try:
        s3.put_object(Bucket=bucket_name, Key=key, Body="This is a placeholder file.")
        print(f"✔ Created placeholder in folder: {key}")
    except Exception as e:
        print(f"❌ Error creating placeholder: {e}")

def create_raw_data_folder(bucket_name):
    raw_data_folder = DEST_PREFIX
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=raw_data_folder)
        if 'Contents' not in response:
            s3.put_object(Bucket=bucket_name, Key=raw_data_folder)
            create_placeholder(bucket_name, raw_data_folder + "placeholder.txt")
            print(f"✔ Created Raw_data folder: {raw_data_folder}")
        else:
            print(f"✔ Raw_data folder already exists: {raw_data_folder}")
    except Exception as e:
        print(f"❌ Error creating Raw_data folder: {e}")

def move_object(bucket_name, source_key, dest_key):
    try:
        s3.copy_object(Bucket=bucket_name, CopySource={"Bucket": bucket_name, "Key": source_key}, Key=dest_key)
        print(f"✔ Moved: {source_key} -> {dest_key}")
        s3.delete_object(Bucket=bucket_name, Key=source_key)
        print(f"🗑 Deleted: {source_key}")
    except Exception as e:
        print(f"❌ Error moving {source_key}: {e}")

def process_file(bucket_name, file_key):
    if not file_key.startswith("Raw_data/") and not file_key.startswith("Derived_data/"):
        dest_key = DEST_PREFIX + file_key
        move_object(bucket_name, file_key, dest_key)

def process_files(bucket_name):
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=SOURCE_PREFIX)
    
    with ThreadPoolExecutor(max_workers=32) as executor:
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    file_key = obj['Key']
                    executor.submit(process_file, bucket_name, file_key)

def main():
    print("🚀 Starting the script to move files and create folder structures.")
    
    start_time = time.time()  # Start timing
    
    create_raw_data_folder(BUCKET_NAME)
    process_files(BUCKET_NAME)
    
    end_time = time.time()  # End timing
    duration = end_time - start_time  # Calculate duration
    
    print(f"✅ All tasks completed successfully in {duration:.2f} seconds.")

if __name__ == "__main__":
    main()
