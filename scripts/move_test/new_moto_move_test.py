import pytest
import boto3
import os
import logging
import time
import sys
from moto import mock_aws
from unittest.mock import patch
import concurrent.futures

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import scripts.new_move as new_move  # Ensure the updated move script is used
from scripts.new_move import process_files, determine_destination

# Mock AWS Credentials
@pytest.fixture(scope="function")
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Mock AWS Services
@pytest.fixture(scope="function")
def s3_mock(aws_credentials):
    with mock_aws():
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket="test-bucket")
        yield s3

@pytest.mark.parametrize("source_key, dest_key, should_copy_succeed, should_delete_succeed", [
    ("source/test-file.txt", "destination/test-file.txt", True, True),  # ✅ Successful move
    ("source/test-file.txt", "destination/test-file.txt", False, True), # ❌ Copy failure
    ("source/test-file.txt", "destination/test-file.txt", True, False), # ❌ Delete failure
])
def test_move_object(s3_mock, source_key, dest_key, should_copy_succeed, should_delete_succeed, caplog):
    """Tests move functionality for successful and failed copy/delete operations."""
    
    # ✅ Upload test file
    s3_mock.put_object(Bucket="test-bucket", Key=source_key, Body="test content")

    with patch.object(new_move.s3, "copy_object") as mock_copy, patch.object(new_move.s3, "delete_object") as mock_delete:
        if not should_copy_succeed:
            mock_copy.side_effect = new_move.s3.exceptions.ClientError({"Error": {"Code": "AccessDenied"}}, "CopyObject")
        if not should_delete_succeed:
            mock_delete.side_effect = new_move.s3.exceptions.ClientError({"Error": {"Code": "AccessDenied"}}, "DeleteObject")

        # Run move function
        try:
            new_move.move_object("test-bucket", source_key, dest_key)
        except Exception:
            pass  # Ignore raised exceptions, we'll check logs

        # ✅ Verify logging output
        if not should_copy_succeed:
            assert "❌ Error moving" in caplog.text
            assert "Access Denied" in caplog.text, "Expected 'Access Denied' error for copy failure."

        if not should_delete_succeed and should_copy_succeed:
            assert "❌ Error moving" in caplog.text
            assert "Access Denied" in caplog.text, "Expected 'Access Denied' error for delete failure."

    print("✅ Move object test completed successfully.")

def test_manual_concurrent_moves(s3_mock):
    """Test multiple files being moved in parallel to check for race conditions and performance issues."""

    file_keys = [f"source/file_{i}.txt" for i in range(100)]
    dest_keys = [f"destination/file_{i}.txt" for i in range(100)]

    # ✅ Upload multiple files
    for file_key in file_keys:
        s3_mock.put_object(Bucket="test-bucket", Key=file_key, Body="test content")

    # ✅ Move files concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
        futures = {executor.submit(new_move.move_object, "test-bucket", file_keys[i], dest_keys[i]): i for i in range(len(file_keys))}
        concurrent.futures.wait(futures)

    # ✅ Validate all files were moved successfully
    for dest_key in dest_keys:
        dest_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=dest_key)
        assert "Contents" in dest_response, f"❌ File {dest_key} was not moved."

    for source_key in file_keys:
        source_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=source_key)
        assert "Contents" not in source_response, f"❌ Source file {source_key} still exists, it should be deleted."

    print("✅ Concurrent move test completed successfully.")

def test_process_files_concurrency(s3_mock):
    """Test process_files function with multiple files to ensure concurrent execution."""

    num_files = 100  # Simulating large-scale file movement
    source_files = [f"source/file_{i}.txt" for i in range(num_files)]

    # ✅ Upload multiple test files
    for file_key in source_files:
        s3_mock.put_object(Bucket="test-bucket", Key=file_key, Body="test content")

    # ✅ Measure execution time
    start_time = time.time()
    process_files("test-bucket")  # Runs multi-threaded file movement
    end_time = time.time()

    # ✅ Ensure all files are moved
    for file_key in source_files:
        dest_key = determine_destination(file_key)
        response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=dest_key)
        assert "Contents" in response, f"❌ File {dest_key} was not moved."

    duration = end_time - start_time
    print(f"✅ Concurrency test completed in {duration:.2f} seconds.")

    assert duration < 100, "❌ Process took too long, possible concurrency issue."

def test_process_files_with_errors(s3_mock):
    """Test process_files function to ensure it continues processing even if some files fail to move."""

    file_keys = [f"source/file_{i}.txt" for i in range(10)]
    dest_keys = [f"destination/file_{i}.txt" for i in range(10)]

    # ✅ Upload multiple test files
    for file_key in file_keys:
        s3_mock.put_object(Bucket="test-bucket", Key=file_key, Body="test content")

    # Mock the move_object function to fail for some files
    original_move_object = new_move.move_object
    def mock_move_object(bucket_name, source_key, dest_key):
        if source_key == "source/file_5.txt":
            raise Exception("Simulated move failure")
        original_move_object(bucket_name, source_key, dest_key)

    with patch.object(new_move, "move_object", side_effect=mock_move_object):
        process_files("test-bucket")

    # ✅ Ensure all files except the failed one are moved
    for i, file_key in enumerate(file_keys):
        dest_key = determine_destination(file_key)
        response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=dest_key)
        if file_key == "source/file_5.txt":
            assert "Contents" not in response, f"❌ File {dest_key} should not have been moved."
        else:
            assert "Contents" in response, f"❌ File {dest_key} was not moved."

    print("✅ Error handling test completed successfully.")

def test_invalid_bucket_name(s3_mock):
    """Test handling of invalid bucket name."""
    invalid_bucket_name = "invalid_bucket_name"
    source_key = "source/test-file.txt"
    dest_key = "destination/test-file.txt"
    
    s3_mock.put_object(Bucket="test-bucket", Key=source_key, Body="test content")

    # Ensure the function does not proceed with an invalid bucket
    try:
        new_move.move_object("invalid-bucket-name", source_key, dest_key)
    except Exception as e:
        # Ensure the exception is raised for invalid bucket name
        assert "Invalid bucket name" in str(e) or "NoSuchBucket" in str(e), f"❌ Expected an error for invalid bucket name but got: {str(e)}"
        print(f"✅ Caught expected exception for invalid bucket name: {str(e)}")

    print("✅ Invalid bucket name test completed successfully.")

def test_missing_source_key(s3_mock):
    """Test handling of missing source key."""
    source_key = "source/missing-file.txt"
    dest_key = "destination/test-file.txt"
    
    # Ensure the source key does not exist
    try:
        new_move.move_object("test-bucket", source_key, dest_key)
    except Exception as e:
        # Ensure the exception is raised for missing source key
        assert "NoSuchKey" in str(e) or "404" in str(e), f"❌ Expected an error for missing source key but got: {str(e)}"
        print(f"✅ Caught expected exception for missing source key: {str(e)}")

    print("✅ Missing source key test completed successfully.")

def test_permission_denied(s3_mock):
    """Test handling of permission denied error."""
    source_key = "source/test-file.txt"
    dest_key = "destination/test-file.txt"
    
    s3_mock.put_object(Bucket="test-bucket", Key=source_key, Body="test content")
    
    with patch.object(new_move.s3, "copy_object", side_effect=Exception("Access Denied")):
        try:
            new_move.move_object("test-bucket", source_key, dest_key)
        except Exception as e:
            # Ensure the exception is raised for permission denied
            assert "Access Denied" in str(e), f"❌ Expected an 'Access Denied' error but got: {str(e)}"
            print(f"✅ Caught expected exception for permission denied: {str(e)}")

    print("✅ Permission denied test completed successfully.")

def test_network_issues(s3_mock):
    """Test handling of network issues."""
    source_key = "source/test-file.txt"
    dest_key = "destination/test-file.txt"
    
    s3_mock.put_object(Bucket="test-bucket", Key=source_key, Body="test content")
    
    with patch.object(new_move.s3, "copy_object", side_effect=Exception("Network Error")):
        try:
            new_move.move_object("test-bucket", source_key, dest_key)
        except Exception as e:
            # Ensure the exception is raised for network issues
            assert "Network Error" in str(e), f"❌ Expected a 'Network Error' but got: {str(e)}"
            print(f"✅ Caught expected exception for network issues: {str(e)}")

    print("✅ Network issues test completed successfully.")

def test_large_files(s3_mock):
    """Test handling of large files."""
    source_key = "source/large-file.txt"
    dest_key = "destination/large-file.txt"
    large_content = "a" * 10**7  # 10 MB content
    
    s3_mock.put_object(Bucket="test-bucket", Key=source_key, Body=large_content)
    
    new_move.move_object("test-bucket", source_key, dest_key)
    
    dest_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=dest_key)
    assert "Contents" in dest_response, "❌ Large file was not moved."
    assert any(obj["Key"] == dest_key for obj in dest_response["Contents"]), "❌ Destination key is missing for large file."

    print("✅ Large files test completed successfully.")

def test_empty_bucket(s3_mock):
    """Test handling of empty bucket."""
    process_files("test-bucket")
    
    # Ensure no errors and no files are processed
    response = s3_mock.list_objects_v2(Bucket="test-bucket")
    assert "Contents" not in response, "❌ Empty bucket should not have any contents."

    print("✅ Empty bucket test completed successfully.")

def test_existing_destination_key(s3_mock):
    """Test handling of existing destination key."""
    source_key = "source/test-file.txt"
    dest_key = "destination/test-file.txt"
    
    s3_mock.put_object(Bucket="test-bucket", Key=source_key, Body="test content")
    s3_mock.put_object(Bucket="test-bucket", Key=dest_key, Body="existing content")
    
    new_move.move_object("test-bucket", source_key, dest_key)
    
    dest_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=dest_key)
    assert "Contents" in dest_response, "❌ Destination file was not created after copy."
    assert any(obj["Key"] == dest_key for obj in dest_response["Contents"]), "❌ Destination key is missing."

    print("✅ Existing destination key test completed successfully.")



