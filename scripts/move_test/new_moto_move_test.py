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
def test_move_object(s3_mock, source_key, dest_key, should_copy_succeed, should_delete_succeed, capsys):
    """Tests move functionality for successful and failed copy/delete operations."""
    
    # ✅ Upload test file
    s3_mock.put_object(Bucket="test-bucket", Key=source_key, Body="test content")

    with patch.object(new_move, "s3") as mock_s3:
        if not should_copy_succeed:
            mock_s3.copy_object.side_effect = Exception("Copy operation failed")
        else:
            mock_s3.copy_object.side_effect = lambda *args, **kwargs: s3_mock.copy_object(*args, **kwargs)

        if not should_delete_succeed:
            mock_s3.delete_object.side_effect = Exception("Delete operation failed")
        else:
            mock_s3.delete_object.side_effect = lambda *args, **kwargs: s3_mock.delete_object(*args, **kwargs)

        try:
            new_move.move_object("test-bucket", source_key, dest_key)
        except Exception as e:
            captured = capsys.readouterr()
            assert str(e) in captured.out, f"❌ Expected error '{e}', but got different output."

    # ✅ Validate file existence
    dest_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=dest_key)
    source_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=source_key)

    if should_copy_succeed:
        assert "Contents" in dest_response, "❌ Destination file was not created after copy."
        assert any(obj["Key"] == dest_key for obj in dest_response["Contents"]), "❌ Destination key is missing."

    if should_delete_succeed and should_copy_succeed:
        assert "Contents" not in source_response, "❌ Source file still exists after successful move."
    else:
        assert "Contents" in source_response, "❌ Source file was deleted despite failure."

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

    num_files = 5000  # Simulating large-scale file movement
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



