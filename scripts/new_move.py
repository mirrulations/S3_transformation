import boto3
import re
import time
import logging
from concurrent.futures import ThreadPoolExecutor

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_output_handler = logging.FileHandler('script_output.log')
file_output_handler.setLevel(logging.INFO)
file_output_handler.setFormatter(log_formatter)

error_output_handler = logging.FileHandler('error_output.log')
error_output_handler.setLevel(logging.ERROR)
error_output_handler.setFormatter(log_formatter)

console_output_handler = logging.StreamHandler()
console_output_handler.setLevel(logging.INFO)
console_output_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_output_handler)
logger.addHandler(error_output_handler)
logger.addHandler(console_output_handler)

# Initialize S3 client
s3 = boto3.client('s3')

BUCKET_NAME = "s3testcs334s25"
SOURCE_PREFIX = ""
RAW_DATA_PREFIX = "raw-data/"
DERIVED_DATA_PREFIX = "derived-data/"

def create_placeholder(bucket_name, key):
    """Creates a placeholder file in the specified folder."""
    try:
        s3.put_object(Bucket=bucket_name, Key=key, Body="This is a placeholder file.")
        logger.info(f"✔ Created placeholder in folder: {key}")
    except Exception as e:
        logger.error(f"❌ Error creating placeholder: {e}")

def create_raw_data_folder(bucket_name):
    """Ensures that Raw_data folder exists in the S3 bucket."""
    raw_data_folder = RAW_DATA_PREFIX
    try:
        s3.put_object(Bucket=bucket_name, Key=raw_data_folder)
        create_placeholder(bucket_name, raw_data_folder + "placeholder.txt")
        logger.info(f"✔ Created Raw_data folder: {raw_data_folder}")
    except Exception as e:
        logger.error(f"❌ Error creating Raw_data folder: {e}")
        
def create_derived_data_folder(bucket_name):
    """Ensures that Derived_data folder exists in the S3 bucket."""
    derived_data_folder = DERIVED_DATA_PREFIX
    try:
        s3.put_object(Bucket=bucket_name, Key=derived_data_folder)
        create_placeholder(bucket_name, derived_data_folder + "placeholder.txt")
        logger.info(f"✔ Created Derived_data folder: {derived_data_folder}")
    except Exception as e:
        logger.error(f"❌ Error creating Derived_data folder: {e}")

def move_object(bucket_name, source_key, dest_key):
    """Moves an object from the source to the destination in S3."""
    try:
        s3.copy_object(Bucket=bucket_name, CopySource={"Bucket": bucket_name, "Key": source_key}, Key=dest_key)
        logger.info(f"✔ Moved: {source_key} -> {dest_key}")
        s3.delete_object(Bucket=bucket_name, Key=source_key)
        logger.info(f"🗑 Deleted: {source_key}")
    except s3.exceptions.NoSuchBucket:
        logger.error(f"❌ Error moving {source_key}: The specified bucket does not exist")
    except s3.exceptions.NoSuchKey:
        logger.error(f"❌ Error moving {source_key}: The specified key does not exist")
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'AccessDenied':
            logger.error(f"❌ Error moving {source_key}: Access Denied")
        else:
            logger.error(f"❌ ClientError moving {source_key}: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error moving {source_key}: {e}")

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
    try:
        if not file_key.startswith(RAW_DATA_PREFIX) and not file_key.startswith(DERIVED_DATA_PREFIX):
            dest_key = determine_destination(file_key)
            move_object(bucket_name, file_key, dest_key)
    except Exception as e:
        logger.error(f"❌ Error processing file {file_key}: {e}")

def process_files(bucket_name):
    """Processes all files in the S3 bucket using multithreading."""
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=SOURCE_PREFIX)
    
    with ThreadPoolExecutor(max_workers=40) as executor:
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    file_key = obj['Key']
                    executor.submit(process_file, bucket_name, file_key)

def main():
    logger.info("🚀 Starting the script to move files and create folder structures.")
    
    start_time = time.time()  # Start timing
    
    # Create necessary folders once
    create_raw_data_folder(BUCKET_NAME)
    create_derived_data_folder(BUCKET_NAME)
    
    process_files(BUCKET_NAME)
    
    end_time = time.time()  # End timing
    duration = end_time - start_time  # Calculate duration
    
    logger.info(f"✅ All tasks completed in {duration:.2f} seconds.")

if __name__ == "__main__":
    main()