import pytest
import boto3
import os
import json
from moto import mock_aws
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from mirrulations_pathgenerator.path_generator import PathGenerator

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

# Helper functions to generate test data
def get_test_docket():
    return {
        "data": {
            "id": "USTR-2015-0010",
            "type": "dockets",
            "attributes": {
                "agencyId": "USTR",
                "docketId": "USTR-2015-0010"
            }
        }
    }

def get_test_document():
    return {
        "data": {
            "id": "USTR-2015-0010-0015",
            "type": "documents",
            "attributes": {
                "agencyId": "USTR",
                "docketId": "USTR-2015-0010"
            }
        }
    }

def get_test_comment():
    return {
        "data": {
            "id": "USTR-2015-0010-0002",
            "type": "comments",
            "attributes": {
                "agencyId": "USTR",
                "docketId": "USTR-2015-0010"
            }
        }
    }

def get_attachment_and_comment():
    link = "https://downloads.regulations.gov/FDA-2017-D-2335-1566/attachment_1.pdf"
    return {
        "data": {
            "id": "FDA-2017-D-2335-1566",
            "type": "comments",
            "attributes": {
                "agencyId": "FDA",
                "docketId": "FDA-2017-D-2335"
            }
        },
        "included": [{
            "attributes": {
                "fileFormats": [{
                    "fileUrl": link
                }]
            }
        }]
    }

# Tests
def test_pathgenerator_docket_json_path(s3_mock):
    """Test generating and uploading a docket JSON path using get_path."""
    path_generator = PathGenerator()
    docket_json = get_test_docket()

    # Generate path using get_path
    generated_path = path_generator.get_path(docket_json)
    expected_path = "Raw_data/USTR/USTR-2015-0010/text-USTR-2015-0010/docket/USTR-2015-0010.json"
    assert generated_path == expected_path

    # Upload to mock S3 bucket
    s3_mock.put_object(Bucket="test-bucket", Key=generated_path, Body=json.dumps(docket_json))

    # Verify upload
    response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=generated_path)
    assert "Contents" in response
    assert any(obj["Key"] == generated_path for obj in response["Contents"])

def test_pathgenerator_document_json_path(s3_mock):
    """Test generating and uploading a document JSON path using get_path."""
    path_generator = PathGenerator()
    document_json = get_test_document()

    # Generate path using get_path
    generated_path = path_generator.get_path(document_json)
    expected_path = "Raw_data/USTR/USTR-2015-0010/text-USTR-2015-0010/documents/USTR-2015-0010-0015.json"
    assert generated_path == expected_path

    # Upload to mock S3 bucket
    s3_mock.put_object(Bucket="test-bucket", Key=generated_path, Body=json.dumps(document_json))

    # Verify upload
    response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=generated_path)
    assert "Contents" in response
    assert any(obj["Key"] == generated_path for obj in response["Contents"])

def test_pathgenerator_comment_json_path(s3_mock):
    """Test generating and uploading a comment JSON path using get_path."""
    path_generator = PathGenerator()
    comment_json = get_test_comment()

    # Generate path using get_path
    generated_path = path_generator.get_path(comment_json)
    expected_path = "Raw_data/USTR/USTR-2015-0010/text-USTR-2015-0010/comments/USTR-2015-0010-0002.json"
    assert generated_path == expected_path

    # Upload to mock S3 bucket
    s3_mock.put_object(Bucket="test-bucket", Key=generated_path, Body=json.dumps(comment_json))

    # Verify upload
    response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=generated_path)
    assert "Contents" in response
    assert any(obj["Key"] == generated_path for obj in response["Contents"])

def test_pathgenerator_attachment_paths(s3_mock):
    """Test generating and uploading attachment paths using get_path."""
    path_generator = PathGenerator()
    attachment_json = get_attachment_and_comment()

    # Generate attachment paths using get_path
    generated_paths = path_generator.get_attachment_json_paths(attachment_json)
    expected_paths = [
        "Raw_data/FDA/FDA-2017-D-2335/binary-FDA-2017-D-2335/comments_attachments/FDA-2017-D-2335-1566_attachment_1.pdf"
    ]
    assert generated_paths == expected_paths

    # Upload attachments to mock S3 bucket
    for path in generated_paths:
        s3_mock.put_object(Bucket="test-bucket", Key=path, Body="Attachment content")

    # Verify uploads
    for path in generated_paths:
        response = s3_mock.list_objects_v2(Bucket="test-bucket", Prefix=path)
        assert "Contents" in response
        assert any(obj["Key"] == path for obj in response["Contents"])