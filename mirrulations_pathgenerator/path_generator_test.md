# PathGenerator Test File Documentation

## Overview
This file contains unit tests for the `PathGenerator` class, which is responsible for generating paths for various types of files (dockets, documents, comments, and attachments) based on a predefined directory structure. The tests use the `moto` library to mock AWS S3 interactions and verify the correctness of the generated paths.

---

## Test File: `path_generator_test.py`

### Description
The test file validates the functionality of the `PathGenerator` class by:
1. Generating paths for different types of JSON files (dockets, documents, comments, and attachments).
2. Uploading the generated paths to a mock S3 bucket.
3. Verifying that the paths are correctly generated and uploaded.

---

### Dependencies
- **`pytest`**: For writing and running unit tests.
- **`boto3`**: AWS SDK for Python, used for interacting with S3.
- **`moto`**: A library for mocking AWS services during testing.
- **`os`**: For environment variable management.
- **`json`**: For handling JSON data.

---

### Fixtures

#### `aws_credentials`
**Scope**: Function  
**Description**:  
Sets up mock AWS credentials for testing. These credentials are required by `boto3` to interact with the mock S3 service.

**Environment Variables**:
- `AWS_ACCESS_KEY_ID`: Mock AWS access key.
- `AWS_SECRET_ACCESS_KEY`: Mock AWS secret access key.
- `AWS_SESSION_TOKEN`: Mock AWS session token.
- `AWS_DEFAULT_REGION`: Mock AWS region.

---

#### `s3_mock`
**Scope**: Function  
**Description**:  
Mocks the AWS S3 service using the `moto` library. Creates a mock S3 bucket named `test-bucket` for testing.

---

### Helper Functions

#### `get_test_docket() -> dict`
**Description**:  
Generates a sample JSON object representing a docket.

**Example Output**:
```json
{
    "data": {
        "id": "USTR-2015-0010",
        "type": "dockets",
        "attributes": {
            "agencyId": "USTR",
            "docketId": "USTR-2015-0010"
        }
    }
}
```

---

#### `get_test_document() -> dict`
**Description**:  
Generates a sample JSON object representing a document.

**Example Output**:
```json
{
    "data": {
        "id": "USTR-2015-0010-0015",
        "type": "documents",
        "attributes": {
            "agencyId": "USTR",
            "docketId": "USTR-2015-0010"
        }
    }
}
```

---

#### `get_test_comment() -> dict`
**Description**:  
Generates a sample JSON object representing a comment.

**Example Output**:
```json
{
    "data": {
        "id": "USTR-2015-0010-0002",
        "type": "comments",
        "attributes": {
            "agencyId": "USTR",
            "docketId": "USTR-2015-0010"
        }
    }
}
```

---

#### `get_attachment_and_comment() -> dict`
**Description**:  
Generates a sample JSON object representing a comment with an attachment.

**Example Output**:
```json
{
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
                "fileUrl": "https://downloads.regulations.gov/FDA-2017-D-2335-1566/attachment_1.pdf"
            }]
        }
    }]
}
```

---

### Tests

#### `test_empty_json(s3_mock)`
**Description**:  
Tests how the `PathGenerator` class handles an empty JSON object.

**Steps**:
1. Pass an empty JSON object to the `get_path` method.
2. Verify that the generated path is `unknown/unknown.json`.

**Expected Path**:
```
unknown/unknown.json
```

---

#### `test_missing_agency_id(s3_mock)`
**Description**:  
Tests how the `PathGenerator` class handles a JSON object without an `agencyId` key.

**Steps**:
1. Pass a JSON object without an `agencyId` key to the `get_attributes` method.
2. Verify that the `agencyId` is set to `unknown`, while `docketId` and `id` are correctly extracted.

**Expected Values**:
- `agencyId`: `"unknown"`
- `docketId`: `"USTR-2015-0010"`
- `id`: `None`

---

#### `test_pathgenerator_docket_json_path(s3_mock)`
**Description**:  
Tests the generation and upload of a docket JSON path using the `get_path` method of the `PathGenerator` class.

**Steps**:
1. Generate a docket path using `get_path`.
2. Upload the generated path to the mock S3 bucket.
3. Verify that the path exists in the mock S3 bucket.

**Expected Path**:
```
Raw_data/USTR/USTR-2015-0010/text-USTR-2015-0010/docket/USTR-2015-0010.json
```

---

#### `test_pathgenerator_document_json_path(s3_mock)`
**Description**:  
Tests the generation and upload of a document JSON path using the `get_path` method of the `PathGenerator` class.

**Steps**:
1. Generate a document path using `get_path`.
2. Upload the generated path to the mock S3 bucket.
3. Verify that the path exists in the mock S3 bucket.

**Expected Path**:
```
Raw_data/USTR/USTR-2015-0010/text-USTR-2015-0010/documents/USTR-2015-0010-0015.json
```

---

#### `test_pathgenerator_comment_json_path(s3_mock)`
**Description**:  
Tests the generation and upload of a comment JSON path using the `get_path` method of the `PathGenerator` class.

**Steps**:
1. Generate a comment path using `get_path`.
2. Upload the generated path to the mock S3 bucket.
3. Verify that the path exists in the mock S3 bucket.

**Expected Path**:
```
Raw_data/USTR/USTR-2015-0010/text-USTR-2015-0010/comments/USTR-2015-0010-0002.json
```

---

#### `test_pathgenerator_attachment_paths(s3_mock)`
**Description**:  
Tests the generation and upload of attachment paths using the `get_attachment_json_paths` method of the `PathGenerator` class.

**Steps**:
1. Generate attachment paths using `get_attachment_json_paths`.
2. Upload the generated paths to the mock S3 bucket.
3. Verify that the paths exist in the mock S3 bucket.

**Expected Paths**:
```
[
    "Raw_data/FDA/FDA-2017-D-2335/binary-FDA-2017-D-2335/comments_attachments/FDA-2017-D-2335-1566_attachment_1.pdf"
]
```

---

### Running the Tests
To run the tests, use the following command:
```bash
python3 -m pytest path_generator_test.py
```

---

### Notes
- The tests use the `moto` library to mock AWS S3 interactions, ensuring that no real AWS resources are used during testing.
- The `get_path` method is tested for dockets, documents, and comments, while `get_attachment_json_paths` is tested for attachments.
- Additional tests ensure that the `PathGenerator` class handles edge cases like missing keys and empty JSON objects gracefully.