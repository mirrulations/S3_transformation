import boto3
import re
import json
from collections import defaultdict
from boto3.s3.transfer import TransferConfig, S3Transfer
from where import determine_raw_path, ensure_s3_path_exists, is_comment_attachment

"""
This script moves files in an S3 bucket to the correct Raw_data folder based on the docket ID.
"""

# Initialize S3 client
s3 = boto3.client('s3')

# Initialize S3Transfer with optimized settings
transfer = S3Transfer(s3, TransferConfig(
    multipart_threshold=50 * 1024 * 1024,  # Files larger than 50MB use multipart uploads
    max_concurrency=16,  # Use up to 16 parallel threads for transfers
))

# Define your S3 bucket and folder names
BUCKET_NAME = "s3testcs334s25"  # 🔹 Replace with your actual bucket name
SOURCE_PREFIX = ""  # 🔹 Empty to scan everything in the bucket
DEST_PREFIX = "Raw_data/"  # 🔹 Move everything into Raw_data/ while preserving structure

# Regex pattern to match docket IDs for the years 2024 and 2025
DOCKET_PATTERN = re.compile(r'([A-Za-z0-9\-]+-(2024|2025)-[A-Za-z0-9\-]+)')

"""
Processes all files in the S3 bucket and moves them to the correct Raw_data folder.
"""

def create_placeholder(bucket_name, key):
    """ Creates a placeholder file in a specific folder. """
    try:
        s3.put_object(Bucket=bucket_name, Key=key, Body="This is a placeholder file.")
        print(f"✔ Created placeholder in folder: {key}")
    except Exception as e:
        print(f"❌ Error creating placeholder: {e}")
        
        
"""
Ensures that the Raw_data folder exists in the S3 bucket.
"""


def create_raw_data_folder(bucket_name):
    """ Ensures that Raw_data folder exists in the S3 bucket. """
    raw_data_folder = f"{DEST_PREFIX}"
    try:
        # Check if the Raw_data folder exists
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=raw_data_folder, Delimiter='/')
        if 'CommonPrefixes' not in response:
            # Create Raw_data folder and add placeholder.txt
            ensure_s3_path_exists(s3, bucket_name, raw_data_folder)
            create_placeholder(bucket_name, raw_data_folder + "placeholder.txt")
            print(f"✔ Created Raw_data folder: {raw_data_folder}")
        else:
            print(f"✔ Raw_data folder already exists: {raw_data_folder}")
    except Exception as e:
        print(f"❌ Error creating Raw_data folder: {e}")
        
"""
move an object in S3 by copying it to a new location and deleting the original.
"""

def move_object(bucket_name, source_key, dest_key):
    """ Moves an object in S3 by copying it to a new location and deleting the original. """
    try:
        # Copy the object using the S3 client
        copy_source = {'Bucket': bucket_name, 'Key': source_key}
        s3.copy(copy_source, bucket_name, dest_key)
        print(f"✔ Moved: {source_key} -> {dest_key}")

        # Delete the original object
        s3.delete_object(Bucket=bucket_name, Key=source_key)
        print(f"🗑 Deleted: {source_key}")

    except Exception as e:
        print(f"❌ Error moving {source_key}: {e}")
        
"""
Determines the data type based on the file name or content.
"""

def determine_data_type(file_name, file_content):
    """ Determines the data type based on the file name or content. """
    extension = file_name.split('.')[-1].lower()
    data_type = 'unknown'
    
    # Define binary file extensions
    binary_extensions = ['pdf', 'doc', 'docx', 'jpeg', 'jpg', 'png']
    
    if extension == 'json':
        try:
            parsed = json.loads(file_content)
            doc_type = parsed['data']['type']
            if doc_type == 'dockets':
                data_type = 'docket'
            elif doc_type == 'documents':
                data_type = 'document'
            elif doc_type == 'comments':
                data_type = 'comment'
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in {file_name}")
        except Exception as e:
            logger.error(f"Error processing JSON file {file_name}: {e}")
    elif extension in binary_extensions:
        if is_comment_attachment(file_name):
            data_type = 'comment'
        else:
            data_type = 'document'
    else:
        data_type = 'text' if extension == 'txt' else 'html'
    
    return data_type


"""
Processes all files in the S3 bucket and moves them to the correct Raw_data folder.
"""


def process_files(bucket_name):
    """ List all objects in the bucket and move those matching the docket pattern. """
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=SOURCE_PREFIX)

    # Collect all unique agencies, excluding Raw_data and Derived_data folders
    agencies = set()
    for page in page_iterator:
        if 'Contents' in page:
            for obj in page['Contents']:
                file_key = obj['Key']
                if not file_key.startswith("Raw_data/") and not file_key.startswith("Derived_data/"):
                    agency = file_key.split('/')[0]  # Extract agency from the key
                    agencies.add(agency)

    # Process each agency separately
    for agency in agencies:
        print(f"Processing agency: {agency}")
        agency_response = s3.list_objects_v2(Bucket=bucket_name, Prefix=f"{agency}/")

        if 'Contents' in agency_response:
            for obj in agency_response['Contents']:
                file_key = obj['Key']
                match = DOCKET_PATTERN.search(file_key)
                if match:
                    docket_id = match.group(1)  # Extract docket ID from file key
                    print(f"Processing docket: {docket_id}")

                    # Determine the destination path using determine_raw_path
                    file_name = file_key.split('/')[-1]
                    extension = file_name.split('.')[-1].lower()

                    # Get the file content
                    file_obj = s3.get_object(Bucket=bucket_name, Key=file_key)
                    if extension == 'json':
                        file_content = file_obj['Body'].read().decode('utf-8')
                    else:
                        file_content = file_obj['Body'].read()

                    # Determine the data type
                    data_type = determine_data_type(file_name, file_content)
                    dest_key = determine_raw_path(file_name, data_type, extension)

                    # Ensure the destination path exists
                    ensure_s3_path_exists(s3, bucket_name, dest_key.rsplit('/', 1)[0])

                    # Move the file to the correct folder
                    move_object(bucket_name, file_key, dest_key)
                else:
                    print(f"No docket ID found in key: {file_key}")
        else:
            print(f"No contents found for agency: {agency}")


"""
Main function to orchestrate the file movement and folder creation process.
"""

def main():
    print("🚀 Starting the script to move files and create folder structures.")
    
    # Ensure Raw_data folder exists
    create_raw_data_folder(BUCKET_NAME)

    # Process and move files
    process_files(BUCKET_NAME)

    print("✅ All tasks completed successfully.")

if __name__ == "__main__":
    main()
