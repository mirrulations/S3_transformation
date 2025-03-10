"""
Unit tests for S3 Path Generator functions.
Tests extract_agency_docket_folder, determine_raw_path, upload_file, 
process_file, and get_s3_client functions.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
from scripts.where import (
    extract_agency_docket_folder,
    determine_raw_path,
    upload_file,
    process_file,
    get_s3_client
)

# Function to print test results
def print_test_result(test_name, expected, actual):
    print(f"\nRunning {test_name}...")
    if expected == actual:
        print(f"✅ {test_name} PASSED")
    else:
        print(f"❌ {test_name} FAILED\nExpected: {expected}\nActual:   {actual}")

# Test
class TestWhere(unittest.TestCase):
    
    """
    Test extract_agency_docket_folder function.
    """
    def test_extract_agency_docket_folder(self):

        # Test document, comment, docket file names
        expected = ("EPA", "EPA-2024-12345")
        actual = extract_agency_docket_folder("EPA-2024-12345-0001.json", "document")
        print_test_result("test_extract_agency_docket_folder (Valid EPA)", expected, actual)
        self.assertEqual(expected, actual)

        expected = ("DHS", "DHS-2023-67890")
        actual = extract_agency_docket_folder("DHS-2023-67890-0010.json", "comment")
        print_test_result("test_extract_agency_docket_folder (Valid DHS)", expected, actual)
        self.assertEqual(expected, actual)

        expected = ("FWS", "FWS-2024-56789")
        actual = extract_agency_docket_folder("FWS-2024-56789.json", "docket")
        print_test_result("test_extract_agency_docket_folder (Valid FWS)", expected, actual)
        self.assertEqual(expected, actual)

        # Test invalid file names
        expected = ("UNKNOWN", "UNKNOWN")
        actual = extract_agency_docket_folder("invalid_file_name.json", "document")
        print_test_result("test_extract_agency_docket_folder (Invalid File Name)", expected, actual)
        self.assertEqual(expected, actual)

        # Test `_content.htm` files
        expected = ("FWS", "FWS-R4-ES-2024-0154")
        actual = extract_agency_docket_folder("FWS-R4-ES-2024-0154-0001_content.htm", "document")
        print_test_result("test_extract_agency_docket_folder (HTM Document)", expected, actual)
        self.assertEqual(expected, actual)

    """
    Test determine_raw_path function.
    """
    def test_determine_raw_path(self):
        # Test docket, document, and comment file placement
        expected = "Raw_data/EPA/EPA-2024-12345/text-EPA-2024-12345/dockets/EPA-2024-12345.json"
        actual = determine_raw_path("EPA-2024-12345.json", "docket", "json")
        print_test_result("test_determine_raw_path (Docket JSON)", expected, actual)
        self.assertEqual(expected, actual)

        expected = "Raw_data/EPA/EPA-2024-12345/binary-EPA-2024-12345/documents_attachments/EPA-2024-12345-attachment.pdf"
        actual = determine_raw_path("EPA-2024-12345-attachment.pdf", "document", "pdf")
        print_test_result("test_determine_raw_path (Document Attachment PDF)", expected, actual)
        self.assertEqual(expected, actual)

        expected = "Raw_data/EPA/EPA-2024-12345/text-EPA-2024-12345/documents/EPA-2024-12345-0001.json"
        actual = determine_raw_path("EPA-2024-12345-0001.json", "document", "json")
        print_test_result("test_determine_raw_path (Document JSON)", expected, actual)
        self.assertEqual(expected, actual)

        # Test `_content.htm` file placement
        expected = "Raw_data/FWS/FWS-R4-ES-2024-0154/text-FWS-R4-ES-2024-0154/documents/FWS-R4-ES-2024-0154-0001_content.htm"
        actual = determine_raw_path("FWS-R4-ES-2024-0154-0001_content.htm", "document", "htm")
        print_test_result("test_determine_raw_path (HTM Document)", expected, actual)
        self.assertEqual(expected, actual)

        # Test comment file placement
        expected = "Raw_data/FWS/FWS-2024-56789/text-FWS-2024-56789/comments/FWS-2024-56789-0001.json"
        actual = determine_raw_path("FWS-2024-56789-0001.json", "comment", "json")
        print_test_result("test_determine_raw_path (Comment JSON)", expected, actual)
        self.assertEqual(expected, actual)

    """
    Test upload_file function.
    """
    @patch("where.boto3.client")  # Mock S3 client
    def test_upload_file(self, mock_boto_client):
        print("\nRunning test_upload_file...")

        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        bucket_name = "test-bucket"
        file_name = "test_upload.txt"
        s3_path = "Raw_data/EPA/EPA-2024-12345/text/test_upload.txt"

        # Create a test file
        with open(file_name, "w") as f:
            f.write("test upload content")

        upload_file(mock_s3, bucket_name, file_name, s3_path)

        # Verify if put_object and upload_file were called
        mock_s3.put_object.assert_called()
        mock_s3.upload_file.assert_called_with(file_name, bucket_name, s3_path)

        print("✅ test_upload_file PASSED")

        os.remove(file_name)

    """
    Test process_file function.
    """
    @patch("where.boto3.client")  # Mock S3 client
    def test_process_file(self, mock_boto_client):
        print("\nRunning test_process_file...")

        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        bucket_name = "test-bucket"
        file_name = "test_process.json"
        file_content = json.dumps({"data": {"type": "documents"}})

        # Create a test file
        with open(file_name, "w") as f:
            f.write(file_content)

        process_file(mock_s3, bucket_name, file_name)

        # Verify S3 upload call
        mock_s3.upload_file.assert_called()

        print("✅ test_process_file PASSED")

        os.remove(file_name)

    """
    Test get_s3_client function.
    """
    @patch("boto3.client")  # Mock S3 client creation
    def test_get_s3_client(self, mock_boto_client):
        print("\nRunning test_get_s3_client...")
        mock_boto_client.return_value = MagicMock()
        client = get_s3_client()
        print(f"Mock S3 Client Created: {'✅ SUCCESS' if client else '❌ FAILURE'}")
        self.assertIsNotNone(client)
        mock_boto_client.assert_called_once_with("s3")

"""
Run the tests.
"""
if __name__ == "__main__":
    print("\n===== Running S3 Path Generator Tests (No AWS Credentials Needed) =====")
    unittest.main(argv=[''], exit=False)
