import boto3
import os
import pytest
import logging
from moto import mock_aws
import sys
import time

"""
This file tests the move.py file using the Moto library.
The tests are written using the pytest framework.
When running this file, you need to make sure to add S3. in front of the where on line 6 of the move.py file.
"""

# Add the path to the transformation_trigger directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from S3.move import (
    create_placeholder,
    create_raw_data_folder,
    move_object,
    process_files,
    determine_data_type
)

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Mock AWS Credentials
@pytest.fixture(scope="function")
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Mock S3
@pytest.fixture(scope="function")
def s3_mock(aws_credentials):
    with mock_aws():
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket="test-bucket")
        yield s3


"""
This function tests the create_placeholder function from the move.py file.
"""
def test_create_placeholder(s3_mock):
    key = "test-folder/placeholder.txt"
    create_placeholder("test-bucket", key)
    response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=key)
    assert "Contents" in response, f"Placeholder file {key} was not created."

"""
This function tests the create_raw_data_folder function from the move.py file.
"""

def test_create_raw_data_folder(s3_mock):
    create_raw_data_folder("test-bucket")
    response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix="Raw_data/")
    assert "Contents" in response or response["KeyCount"] > 0, "Raw_data folder was not created."

"""
This function tests the move_object function from the move.py file.
"""

def test_move_object(s3_mock):
    source_key = "source/test-file.txt"
    dest_key = "destination/test-file.txt"
    s3_mock.put_object(Bucket="test-bucket", Key=source_key, Body="test content")
    move_object("test-bucket", source_key, dest_key)
    
    dest_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=dest_key)
    source_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=source_key)
    
    assert "Contents" in dest_response, "File was not moved to the destination."
    assert "Contents" not in source_response, "File was not deleted from the source."

"""
This function tests the determine_data_type function from the move.py file.
"""

def test_determine_data_type():
    assert determine_data_type("test.json", '{"data": {"type": "dockets"}}') == "docket"
    assert determine_data_type("test.pdf", "") == "document"
    assert determine_data_type("test.txt", "") == "text"




"""
This function tests the process_files function from the move.py file.
"""
def test_process_files(s3_mock):
    # Keys for the files in S3, adjusted to match your directory structure
    json_key = "EPA/EPA-HQ-OGC-2025-0019/text-EPA-HQ-OGC-2025-0019/docket/EPA-HQ-OGC-2025-0019.json"
    pdf_key = "EPA/EPA-HQ-OGC-2025-0019/binary-EPA-HQ-OGC-2025-0019/comment_attachments/EPA-HQ-OGC-2025-0019-0003_attachment_1.pdf"

    # Put objects in S3
    s3_mock.put_object(Bucket="test-bucket", Key=json_key, Body='{"data": {"type": "dockets"}}')
    s3_mock.put_object(Bucket="test-bucket", Key=pdf_key, Body="test content")

    # Process the files (mocking the file move inside process_files if needed)
    process_files("test-bucket")

    # Define destination paths, adjusted for your file structure
    json_dest = "Raw_data/EPA/EPA-HQ-OGC-2025-0019/text-EPA-HQ-OGC-2025-0019/dockets/EPA-HQ-OGC-2025-0019.json"
    pdf_dest = "Raw_data/EPA/EPA-HQ-OGC-2025-0019/binary-EPA-HQ-OGC-2025-0019/comments_attachments/EPA-HQ-OGC-2025-0019-0003_attachment_1.pdf"

    # Wait for the file to "appear" at the destination (to avoid timing issues)
    retries = 10  # Increase the retry count
    for _ in range(retries):
        json_response = s3_mock.list_objects_v2(Bucket="test-bucket")
        pdf_response = s3_mock.list_objects_v2(Bucket="test-bucket")

        # If the files are found, break out of the loop
        if "Contents" in json_response and "Contents" in pdf_response:
            break
        time.sleep(2)  # Increase wait time between retries (e.g., 2 seconds)

    # Log the actual keys in the response for debugging
    print("JSON response keys:", [item['Key'] for item in json_response.get('Contents', [])])
    print("PDF response keys:", [item['Key'] for item in pdf_response.get('Contents', [])])

    # Check if the key inside Contents matches the expected destination for JSON file
    json_found = any(item['Key'].startswith(json_dest) for item in json_response.get('Contents', []))
    pdf_found = any(item['Key'].startswith(pdf_dest) for item in pdf_response.get('Contents', []))

    # Assert that both JSON and PDF files were moved successfully
    assert json_found, \
        f"JSON file was not moved correctly: found: {[item['Key'] for item in json_response.get('Contents', [])]}"
    assert pdf_found, \
        f"PDF file was not moved correctly: found: {[item['Key'] for item in pdf_response.get('Contents', [])]}"


# If the script is being executed directly, run pytest
if __name__ == "__main__":
    pytest.main(["-v"])  # Use "-v" for more detailed output
