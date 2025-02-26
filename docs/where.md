# S3 Where Functionality for Mirrulations Project

The `where.py` file generates complex S3 path structures for file uploads based on raw data standards . It is designed to handle multiple file types—including JSON files, text files, and binary attachments (such as PDFs, DOCs, images, etc.)—and organizes them into designated folders in S3. Special handling is provided for comment attachments.

## Overview

- **Purpose:**  
  Determine and create the proper S3 destination paths for files based on their content, naming convention, and file type. The code supports files that represent dockets, documents, comments, and various attachments. For comment attachments (which follow a specific naming pattern), the file is routed into a dedicated folder within the S3 structure.

- **Key Behaviors:**  
  - Extracts agency and docket information from file names.
  - Determines file type based on both file extension and, for JSON files, the content of the file.
  - Uses regular expressions to detect comment attachments (files ending with a pattern like `_attachment_#.<extension>`).
  - Constructs S3 paths that segregate files by type:
    - **Dockets:** Placed under a `dockets` folder.
    - **Documents and HTML content:** Placed under a `documents` folder.
    - **Comments:** Placed under a `comments` folder.
    - **Attachments:**  
      - Comment attachments are stored in a `comments_attachments` folder within a binary folder.
      - Other attachments are stored in a `documents_attachments` folder.
  - Ensures the appropriate S3 folder structure exists before attempting file uploads.
  - Provides logging at key stages (such as path generation, S3 folder creation, and file upload) to aid in debugging and traceability.

## Usage

If you want to run this on its own it accepts two command-line arguments(where.py integrated into move.py):
1. **Filename:** The local path of the file to be processed.
2. **S3 Bucket:** The target S3 bucket name.

### Example

To process a file named `VA-2025-VBA-0006-0011_attachment_1.pdf` and upload it to an S3 bucket called `my-bucket`, run:

```bash
python3 where.py VA-2025-VBA-0006-0011_attachment_1.pdf my-bucket
```
### Tests
- Naviagte to `where_tests` folder:
  - Command to run `where_test.py`:
    ```bash
    python3 where_test.py
    ```

  - Command to run `where_moto_testing.py`:
    ```bash
    python3 -m pytest --log-cli-level=DEBUG where_moto_testing.py
    ```


