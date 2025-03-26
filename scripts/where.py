"""
Updated S3 Path Generator for Mirrulations Project
Handles complex S3 path structures based on raw data standards.
"""

import boto3
import json
import logging
import os
import re
import sys
from botocore.exceptions import BotoCoreError, ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAW_PREFIX = 'raw-data/'

def is_comment_attachment(file_name):
    """
    Returns True if the file_name matches the comment attachment pattern.
    Example: VA-2025-VBA-0006-0011_attachment_1.pdf
    """
    pattern = r'.+_attachment_\d+\.[^.]+$'
    return re.match(pattern, file_name) is not None

"""
Extracts the agency name and docket folder from the filename.

- **Docket JSON:** `docket_folder = full name without extension`
- **Other JSONs (comments, documents, etc.):** `docket_folder = full name without last part`
- **HTM files ending in `_content.htm` go in "documents" folder**
"""
def extract_agency_docket_folder(file_name, data_type):
    file_name = re.sub(r'_attachment_\d+\.[^.]+$', '', file_name)  # Remove attachment suffix
    file_name = file_name.replace('.json', '').replace('_content.htm', '') # Remove extensions
    parts = file_name.split('-')

    if len(parts) < 3:
        return "UNKNOWN", "UNKNOWN"

    agency = parts[0]

    if data_type == 'docket':
        docket_folder = '-'.join(parts)  # Keep full name
    elif data_type == 'document' or file_name.endswith("_content"):
        docket_folder = '-'.join(parts[:-1])  # Remove last part (document ID)
    else:
        docket_folder = '-'.join(parts[:-1])  # Remove last part for comments and other types

    return agency, docket_folder

"""
Determines the correct S3 path for the given file.
"""
def determine_raw_path(file_name, data_type, extension):
    agency, docket_folder = extract_agency_docket_folder(file_name, data_type)

    # Handle attachments
    if is_comment_attachment(file_name):
        # This is a comment attachment: place in "comment_attachments" folder inside binary-docket_folder.
        folder = 'comments_attachments'
        return f"{RAW_PREFIX}{agency}/{docket_folder}/binary-{docket_folder}/{folder}/{file_name}"
    elif 'attachment' in file_name:
        # Otherwise, treat as a document attachment.
        folder = 'documents_attachments'
        return f"{RAW_PREFIX}{agency}/{docket_folder}/binary-{docket_folder}/{folder}/{file_name}"

    # Handle HTM files ending in "_content.htm"
    if extension == 'htm' and file_name.endswith('_content.htm'):
        folder = 'documents'
    else:
        folder = {
            'docket': 'dockets',
            'document': 'documents',
            'comment': 'comments'
        }.get(data_type, 'unknown')

    return f"{RAW_PREFIX}{agency}/{docket_folder}/text-{docket_folder}/{folder}/{file_name}"

"""
Ensures that the specified S3 path exists.
"""
def ensure_s3_path_exists(s3_client, bucket, path):
    try:
        s3_client.put_object(Bucket=bucket, Key=(path if path.endswith('/') else path + '/'))
        logger.info(f"Ensured path exists: {path}")
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to ensure path {path}: {e}")

"""
Uploads a file to the specified S3 path.
"""
def upload_file(s3_client, bucket, file_path, s3_path):
    try:
        ensure_s3_path_exists(s3_client, bucket, os.path.dirname(s3_path))
        s3_client.upload_file(file_path, bucket, s3_path)
        logger.info(f"Uploaded {file_path} to {s3_path}")
    except (BotoCoreError, ClientError) as e:
        logger.error(f"S3 upload failed: {e}")

"""
Processes a file to determine its type and uploads it to the appropriate S3 location.
"""
def process_file(s3_client, bucket, file_path):
    file_name = os.path.basename(file_path)
    extension = file_name.split('.')[-1].lower()
    data_type = 'unknown'
    
    # Define binary file extensions
    binary_extensions = ['pdf', 'doc', 'docx', 'jpeg', 'jpg', 'png']
    
    if extension == 'json':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                parsed = json.loads(content)
                doc_type = parsed['data']['type']
                if doc_type == 'dockets':
                    data_type = 'docket'
                elif doc_type == 'documents':
                    data_type = 'document'
                elif doc_type == 'comments':
                    data_type = 'comment'
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format in {file_path}")
                return
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return
    elif extension in binary_extensions:
        # For binary files, do not attempt to read as text.
        # Use the file name to determine the type if it's an attachment.
        if is_comment_attachment(file_name):
            data_type = 'comment'
        else:
            data_type = 'document'
    else:
        # For other text-based files, handle them as text.
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                _ = f.read()  # You may not need the content for non-json types.
            data_type = 'text' if extension == 'txt' else 'html'
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return

    s3_path = determine_raw_path(file_name, data_type, extension)
    upload_file(s3_client, bucket, file_path, s3_path)

"""
Creates and returns an S3 client.
"""
def get_s3_client():
    try:
        return boto3.client('s3')
    except Exception as e:
        logger.error(f"Error creating S3 client: {e}")
        raise

"""
Main function to process a file and upload it to S3.
- takes in the filename and S3 bucket name as arguments.
"""
def main():
    if len(sys.argv) != 3:
        print("Usage: python3 script.py <filename> <s3bucket>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    bucket = sys.argv[2]
    
    s3_client = get_s3_client()
    process_file(s3_client, bucket, file_path)

if __name__ == "__main__":
    main()
