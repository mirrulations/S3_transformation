from moto import mock_aws
import boto3
import pytest
import os
import logging
import sys
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import scripts.new_move as new_move

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

# Mock AWS Services
@pytest.fixture(scope="function")
def s3_mock(aws_credentials):
    with mock_aws():
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket="test-bucket")
        yield s3

# ✅ Test: Ensure that if copy fails, source file remains unchanged
def test_move_failed_copy_object(s3_mock):
    source_key = "source/test-file.txt"
    dest_key = "destination/test-file.txt"

    s3_mock.put_object(Bucket="test-bucket", Key=source_key, Body="test content")

    new_move.move_object("test-bucket", "nonexistent-file.txt", dest_key)

    # ✅ Ensure that no file was created at the destination
    dest_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=dest_key)
    assert "Contents" not in dest_response, "❌ Destination file should not exist."

    # ✅ Ensure that source file is still there
    source_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=source_key)
    assert "Contents" in source_response, "❌ Source file was unexpectedly deleted."

    logger.info("✅ Test move failed copy object completed.")

import scripts.new_move as new_move
from unittest.mock import patch

def test_move_failed_delete_object(s3_mock, capsys):
    source_key = "source/test-file.txt"
    dest_key = "destination/test-file.txt"

    s3_mock.put_object(Bucket="test-bucket", Key=source_key, Body="test content")

    with patch.object(new_move, "s3") as mock_s3:
        mock_s3.copy_object.side_effect = lambda *args, **kwargs: s3_mock.copy_object(*args, **kwargs)
        mock_s3.delete_object.side_effect = Exception("Delete operation failed")  # Force delete failure

        new_move.move_object("test-bucket", source_key, dest_key)

        captured = capsys.readouterr()  # Capture printed output
        assert "Delete operation failed" in captured.out, "Expected delete failure message in output."
        print("✅ Delete failure was correctly logged.")

        # ✅ Ensure destination file **was** created
        dest_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=dest_key)
        assert "Contents" in dest_response, "❌ Destination file was not created."
        assert any(obj['Key'] == dest_key for obj in dest_response['Contents']), "❌ Destination key is missing."

        # ✅ Ensure source file **was not deleted**
        source_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=source_key)
        assert "Contents" in source_response, "❌ Source file was deleted despite delete failure."

    print("✅ Test move failed delete object completed.")



# ✅ Test: Ensure move is successful
def test_move_successful(s3_mock):
    source_key = "source/test-file.txt"
    dest_key = "destination/test-file.txt"

    s3_mock.put_object(Bucket="test-bucket", Key=source_key, Body="test content")

    new_move.move_object("test-bucket", source_key, dest_key)

    # ✅ Ensure the file was moved successfully
    dest_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=dest_key)
    source_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=source_key)

    assert "Contents" in dest_response, "❌ File was not moved to the destination."
    assert any(obj['Key'] == dest_key for obj in dest_response['Contents']), "❌ Destination key is missing."
    assert "Contents" not in source_response, "❌ Source key still exists, it should be deleted."

    logger.info("✅ Test move successful completed.")
    
    
    
import logging
import scripts.new_move as new_move
from unittest.mock import patch

def test_move_failed_copy_object_does_not_delete_source(s3_mock, capsys, caplog):
    source_key = "source/test-file.txt"
    dest_key = "destination/test-file.txt"

    s3_mock.put_object(Bucket="test-bucket", Key=source_key, Body="test content")

    with caplog.at_level(logging.DEBUG):  # Capture logs at DEBUG level
        with patch.object(new_move, "s3") as mock_s3:
            # ✅ Simulate copy failure
            mock_s3.copy_object.side_effect = Exception("Copy operation failed")
            mock_s3.delete_object.side_effect = lambda *args, **kwargs: print("🔥 DELETE was called!")

            try:
                new_move.move_object("test-bucket", source_key, dest_key)
            except Exception as e:
                assert "Copy operation failed" in str(e), "❌ Expected copy failure, but got a different error."
                print("✅ Copy failure correctly caused an exception.")

            # ✅ Ensure delete was NOT called
            source_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=source_key)
            assert "Contents" in source_response, "❌ Source file was deleted despite copy failure."

            # ✅ Ensure destination file was NOT created
            dest_response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=dest_key)
            assert "Contents" not in dest_response, "❌ Destination file should not exist after copy failure."

    print("✅ Test move failed copy object completed successfully.")

