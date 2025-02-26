# Move Functionality for Mirrulations Project

The `move.py` file handles the transfer of files to an S3 bucket after determining the appropriate file destination paths using the logic defined in `where.py`. It processes files based on the specific structure and ensures that they are uploaded to the correct folders in S3, including managing any potential errors or retries during the process.

## Overview

- **Purpose:**  
  The primary purpose of `move.py` is to facilitate the movement of files to S3, ensuring they are placed in the correct path based on file type and content. It integrates with `where.py` to leverage the S3 destination paths generated based on file names and content. It supports both simple files and complex file types, including JSON files, documents, and binary attachments (e.g., PDFs, DOCs).

- **Key Behaviors:**  
  - Calls `where.py` to determine the S3 destination paths for files based on their content and naming convention.
  - Handles different types of file uploads, ensuring they are placed in designated S3 folders (e.g., `dockets`, `documents`, `comments`).
  - Provides error handling in case of failed uploads, with automatic retries for temporary issues.
  - Ensures that the destination folder exists in S3 before attempting an upload.
  - Logs all key actions and statuses during the file transfer process to aid with debugging and provide traceability.


## moto_move_test Setup


```bash
# When running this file, you need to make sure to add S3. in front of the where on line 6 of the move.py file.
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment (Linux/macOS)
source .venv/bin/activate

# Activate the virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
pip install boto3 moto pytest

# Run python file
python3 moto_move_test.py

```

## Setup

Before running `move.py`, set up a virtual environment and install the required dependencies:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment (Linux/macOS)
source .venv/bin/activate

# Activate the virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
pip install boto3

# run file 

python3 move.py

```



