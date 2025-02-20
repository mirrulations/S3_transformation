import boto3
import re

# AWS S3 Configuration
S3_BUCKET = "mirrulations-test1"
s3_client = boto3.client("s3")

# Old and New Structure Prefixes
RAW_PREFIX = "Raw_data/"
DERIVED_PREFIX = "Derived_data/"

# Function to list files in an S3 prefix (with optional limit)
def list_s3_files(prefix, max_files=5000):  # Limits results for efficiency
    files = []
    paginator = s3_client.get_paginator("list_objects_v2")

    file_count = 0
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        if "Contents" in page:
            for obj in page["Contents"]:
                files.append(obj["Key"])
                file_count += 1
                if file_count >= max_files:  # Stop after max_files
                    print(f"Reached max file limit ({max_files}) while listing files.")
                    return files
    return files

# Function to ensure a path exists in S3 by checking first
def ensure_s3_path_exists(prefix):
    existing_files = list_s3_files(prefix, max_files=1)  # Check if files exist
    if existing_files:
        return  # Folder already exists, no need to upload a placeholder

    temp_placeholder = "/tmp/placeholder.txt"
    with open(temp_placeholder, "w") as f:
        f.write("Placeholder to ensure S3 structure exists.")
    s3_client.upload_file(temp_placeholder, S3_BUCKET, f"{prefix}placeholder.txt")
    print(f"Created placeholder in: {prefix}")

# Function to move extracted comment text to Derived_data
def move_extracted_comments():
    raw_files = list_s3_files(RAW_PREFIX)

    for file_key in raw_files:
        if "/comments_extracted_text/" in file_key:
            try:
                parts = file_key.split("/")
                agency = parts[1]
                docket_id = parts[2].replace("text-", "")
                extracted_filename = parts[-1]
                new_filename = re.sub(r"_extracted", "", extracted_filename)

                derived_base_path = f"{DERIVED_PREFIX}{agency}/{docket_id}/mirrulations/extracted_txt/comment_attachment/"
                ensure_s3_path_exists(derived_base_path)

                new_key = f"{derived_base_path}{new_filename}"
                
                # Use copy instead of download/upload for speed
                s3_client.copy_object(
                    Bucket=S3_BUCKET,
                    CopySource={"Bucket": S3_BUCKET, "Key": file_key},
                    Key=new_key
                )
                
                # Delete original file after copying
                s3_client.delete_object(Bucket=S3_BUCKET, Key=file_key)

                print(f"Moved: {file_key} -> {new_key}")

            except Exception as e:
                print(f"Failed to move {file_key} due to error: {e}")

# Function to restructure Raw_data by renaming and moving files
def restructure_raw_data():
    raw_files = list_s3_files(RAW_PREFIX)

    for file_key in raw_files:
        parts = file_key.split("/")
        
        # Ensure we are working with valid docket folders and not affecting binary/text structure
        if len(parts) < 3:
            continue  # Skip invalid file paths

        agency, docket_folder = parts[1], parts[2]

        # Only process files inside 'text-<docket_id>', leave binary/text structure untouched
        if docket_folder.startswith("text-") and "/comments_extracted_text/" not in file_key:
            docket_id = docket_folder.replace("text-", "")
            new_key = file_key.replace(f"text-{docket_id}/", f"text-{docket_id}/")  # Preserve folder structure

            if new_key != file_key:  # Ensure we are actually renaming something
                s3_client.copy_object(
                    Bucket=S3_BUCKET, 
                    CopySource={"Bucket": S3_BUCKET, "Key": file_key}, 
                    Key=new_key
                )
                s3_client.delete_object(Bucket=S3_BUCKET, Key=file_key)

                print(f"Reformatted: {file_key} -> {new_key}")

    print("Raw data restructuring completed.")

# Function to create the full Derived_data structure
def create_derived_structure():
    base_dirs = ["MoravianResearch", "mirrulations", "trotterf"]
    sub_dirs = {
        "MoravianResearch": ["projectName/comment", "projectName/docket", "projectName/document"],
        "mirrulations": [
            "ai_summary/comment", "ai_summary/comment_attachments", "ai_summary/document",
            "entities/comment", "entities/comment_attachment", "entities/document",
            "extracted_txt/comment_attachment"
        ],
        "trotterf": ["projectName/fileType"]
    }
    
    # Get unique agency & docket directories
    agencies = set()
    raw_files = list_s3_files(RAW_PREFIX)
    for file_key in raw_files:
        parts = file_key.split("/")
        if len(parts) > 2:
            agencies.add((parts[1], parts[2].replace("text-", "")))

    # Create derived directories
    for agency, docket_id in agencies:
        for base in base_dirs:
            for sub in sub_dirs[base]:
                derived_path = f"{DERIVED_PREFIX}{agency}/{docket_id}/{base}/{sub}/"
                ensure_s3_path_exists(derived_path)

    print("Derived structure creation completed.")

if __name__ == "__main__":
    print("Starting data migration...")

    create_derived_structure()
    print("Derived structure created.")

    move_extracted_comments()
    print("Extracted comments moved.")

    restructure_raw_data()
    print("Raw data reformatted.")

    print("All tasks completed successfully!")
