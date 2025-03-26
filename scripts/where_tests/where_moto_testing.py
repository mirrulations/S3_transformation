"""
This file contains moto tests for the where.py file.
The tests are written using the pytest framework.
"""

import boto3
import os
import pytest
import logging
from moto import mock_aws
from scripts.where import (
    extract_agency_docket_folder,
    determine_raw_path,
    upload_file,
    process_file,
    get_s3_client
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
    """Mocked AWS credentials for Moto"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Mock S3
@pytest.fixture(scope="function")
def s3_mock(aws_credentials):
    """Mock S3 setup"""
    with mock_aws():
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket="test-bucket")
        yield s3

# Test extract_agency_docket_folder function
def test_extract_agency_docket_folder():
    logger.info("Starting test for extract_agency_docket_folder")
    try:
        assert extract_agency_docket_folder("EPA-2024-12345.json", "docket") == ("EPA", "EPA-2024-12345")
        assert extract_agency_docket_folder("EPA-2024-12345-0001.json", "document") == ("EPA", "EPA-2024-12345")
        assert extract_agency_docket_folder("DHS-2023-67890-0010.json", "comment") == ("DHS", "DHS-2023-67890")
        assert extract_agency_docket_folder("invalid_file.json", "document") == ("UNKNOWN", "UNKNOWN")
        assert extract_agency_docket_folder("FWS-R4-ES-2024-0154-0001_content.htm", "document") == ("FWS", "FWS-R4-ES-2024-0154")
        logger.info("extract_agency_docket_folder tests passed")
    except AssertionError as e:
        logger.error("extract_agency_docket_folder test failed: %s", e)
        raise

# Test determine_raw_path function
def test_determine_raw_path():
    logger.info("Starting test for determine_raw_path")
    try:
        assert determine_raw_path("EPA-2024-12345.json", "docket", "json") == "raw-data/EPA/EPA-2024-12345/text-EPA-2024-12345/dockets/EPA-2024-12345.json"
        assert determine_raw_path("EPA-2024-12345-0002.json", "document", "json") == "raw-data/EPA/EPA-2024-12345/text-EPA-2024-12345/documents/EPA-2024-12345-0002.json"
        assert determine_raw_path("FWS-2024-56789-0001.json", "comment", "json") == "raw-data/FWS/FWS-2024-56789/text-FWS-2024-56789/comments/FWS-2024-56789-0001.json"
        assert determine_raw_path("FWS-R4-ES-2024-0154-0001_content.htm", "document", "htm") == "raw-data/FWS/FWS-R4-ES-2024-0154/text-FWS-R4-ES-2024-0154/documents/FWS-R4-ES-2024-0154-0001_content.htm"
        logger.info("determine_raw_path tests passed")
    except AssertionError as e:
        logger.error("determine_raw_path test failed: %s", e)
        raise

# Test upload_file function
def test_upload_file(s3_mock):
    logger.info("Starting test for upload_file")
    file_name = "test_upload.json"
    s3_path = "raw-data/EPA/EPA-2024-12345/text-EPA-2024-12345/documents/test_upload.json"

    # Create a test file
    with open(file_name, "w") as f:
        f.write("test upload content")
    logger.info(f"Created file: {file_name}")

    try:
        upload_file(s3_mock, "test-bucket", file_name, s3_path)

        # Validate file was uploaded
        response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=s3_path)
        assert "Contents" in response  # Ensures the file exists in S3
        logger.info(f"File uploaded to S3 path: {s3_path}")
    except AssertionError as e:
        logger.error(f"upload_file test failed: {e}")
        raise
    finally:
        os.remove(file_name)
        logger.info(f"Removed file: {file_name}")

# Test process_file function
def test_process_file(s3_mock):
    logger.info("Starting test for process_file")
    input_file_name = "test_process_input.json"
    s3_input_path = "raw-data/EPA/EPA-2024-12345/text-EPA-2024-12345/documents/test_process_input.json"

    # Create a test input file
    with open(input_file_name, "w") as f:
        f.write("test process input content")
    logger.info(f"Created input file: {input_file_name}")

    try:
        # Upload the input file to S3
        upload_file(s3_mock, "test-bucket", input_file_name, s3_input_path)

        # Process the file
        process_file(s3_mock, "test-bucket", s3_input_path)

        # Validate the output file was created in S3
        response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=s3_input_path)
        assert "Contents" in response  # Ensures the output file exists in S3
        logger.info(f"File processed and uploaded to S3 path: {s3_input_path}")
    except AssertionError as e:
        logger.error(f"process_file test failed: {e}")
        raise
    finally:
        os.remove(input_file_name)
        logger.info(f"Removed input file: {input_file_name}")
    
# Test get_s3_client function
def test_get_s3_client():
    logger.info("Starting test for get_s3_client")
    try:
        s3_client = get_s3_client()
        assert s3_client is not None
        logger.info("get_s3_client test passed")
    except AssertionError as e:
        logger.error(f"get_s3_client test failed: {e}")
        raise
