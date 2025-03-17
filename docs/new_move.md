# Documentation: new_move.py

## Overview
This script handles the movement of files within an S3 bucket. It ensures that certain folder structures are created, processes files based on their paths, and moves them to appropriate destinations within the bucket. The code utilizes AWS S3's `copy_object` and `delete_object` methods, handles errors robustly, and optimizes performance with multithreading.

## Code Reliability and Test Coverage

### 1. **Mocking AWS Services**:
   - AWS credentials are mocked using `moto` to simulate interactions with AWS services without affecting real resources.
   - AWS S3 is mocked to simulate S3 operations like `copy_object` and `delete_object` for testing.

### 2. **Test Cases for Reliability**:
   The following key scenarios are tested to ensure the code performs reliably:

   #### a. **Move Object Test**:
   - **Success**: Verifies that files are successfully copied and deleted.
   - **Failure (Copy/Deletion Error)**: Tests scenarios where the copy or delete operation fails due to permissions or access issues. Errors are logged, and the expected messages are validated.
   - **Error Logging**: Ensures that appropriate error messages, such as "Access Denied" or "ClientError," are logged when an operation fails.

   #### b. **Concurrent File Moves**:
   - **Parallel Processing**: Multiple files are moved in parallel to identify race conditions or performance issues. The test ensures that all files are successfully moved and no errors occur.

   #### c. **Process Files Concurrency**:
   - **Large-Scale File Movement**: Simulates the movement of 100 files concurrently, validating that the code performs as expected within a reasonable execution time. This test ensures the efficiency of the multithreaded file processing.

   #### d. **Error Handling in `process_files`**:
   - **Partial Success**: Simulates a failure for one file during processing. Verifies that other files continue to be processed successfully even if one file fails.
   - **Tested Scenarios**: The system handles missing files, invalid bucket names, and network issues.

   #### e. **Error Handling for Missing or Invalid Keys**:
   - **Missing Source Key**: Tests how the code handles when a source file doesn't exist in S3.
   - **Invalid Bucket**: Simulates interactions with an invalid bucket name and ensures proper error handling.

   #### f. **Network and Permission Errors**:
   - Simulates permission denied and network error scenarios and ensures that the errors are handled and logged correctly.

   #### g. **Handling Large Files**:
   - Tests the movement of large files (e.g., 10 MB) to ensure the system can handle them efficiently.

   #### h. **Empty Bucket Handling**:
   - Verifies that when the bucket is empty, no errors occur, and no unnecessary operations are attempted.

   #### i. **Existing Destination Key**:
   - Tests how the system handles files when the destination key already exists, ensuring the file is correctly overwritten or skipped as per the logic.

---

## Main Code Functions

### 1. **`create_placeholder`**:
   Creates a placeholder file in the specified S3 folder, ensuring folder structures are maintained even when empty.

### 2. **`create_raw_data_folder`**:
   Ensures the `Raw_data` folder exists in the S3 bucket. If the folder doesn't exist, it is created along with a placeholder file.

### 3. **`create_derived_data_folder`**:
   Similar to `create_raw_data_folder`, this function ensures the `Derived_data` folder exists and creates a placeholder.

### 4. **`move_object`**:
   Moves a file from the source to the destination within the S3 bucket using the `copy_object` and `delete_object` methods. The function handles different exceptions like `NoSuchBucket`, `NoSuchKey`, and `AccessDenied`, logging detailed error messages.

### 5. **`determine_destination`**:
   Determines the appropriate destination for a file based on its key. If the file contains `extracted_text` in its path, it is placed in the `Derived_data` folder; otherwise, it is moved to the `Raw_data` folder.

### 6. **`process_file`**:
   Processes an individual file and moves it to its determined destination.

### 7. **`process_files`**:
   Processes all files in the specified S3 bucket using multithreading (`ThreadPoolExecutor`) to improve performance. This function paginates through the files in the source folder and processes them concurrently.

### 8. **`main`**:
   This is the main entry point for the script. It starts by creating necessary folders, processes all files, and logs the time taken for execution.

---

## Error Handling
The code is designed to handle various errors gracefully:
- **Permission Issues**: Errors like "Access Denied" are logged, and the process continues without crashing.
- **Network Issues**: Simulates network errors and verifies that they are handled properly.
- **Invalid Bucket or Key**: The code raises and logs specific exceptions when the bucket or file key is invalid.

---

## Test Coverage

| Test Case                                     | Description                                                                 |
|-----------------------------------------------|-----------------------------------------------------------------------------|
| **test_move_object**                          | Verifies moving files, handling copy and delete errors.                     |
| **test_manual_concurrent_moves**              | Tests the parallel movement of multiple files to ensure no race conditions. |
| **test_process_files_concurrency**           | Verifies concurrent execution and efficiency when processing many files.    |
| **test_process_files_with_errors**           | Ensures that errors in some files do not block the movement of others.      |
| **test_invalid_bucket_name**                 | Tests handling of invalid bucket names.                                     |
| **test_missing_source_key**                  | Verifies that missing source keys are handled properly.                     |
| **test_permission_denied**                   | Simulates permission-denied errors to test error handling.                  |
| **test_network_issues**                      | Tests how the code handles network errors during file operations.           |
| **test_large_files**                         | Verifies that large files are moved correctly without errors.               |
| **test_empty_bucket**                        | Tests behavior when no files are in the bucket.                             |
| **test_existing_destination_key**            | Tests how the code handles existing destination keys.                       |

## Run test command(make sure to install requirements in virtual env):
  - ```bash 
    python3 -m pytest --log-cli-level=DEBUG new_moto_move_test.py
    ```

## Approximated run time with parallelization
  - Workers: 40
  - run time on 6247 files - 30 seconds
  - Rate: 
    - 6247 files/30 seconds ≈ 208.23 files per second
  - Estimated time for 28,000,000 files: 
    - 28,000,000 files/ 208.23 files per second ≈ 134,450 seconds
  - Converting to Hours and Days: 
    - 134,450 seconds ≈ 2,240 minutes
    - 2,240 minutes ≈ 37.3 hours
    - 37.3 hours ≈ 1.55 days
---

## Conclusion
The system is reliable and efficient, with robust error handling and multithreading to ensure scalability and performance. The extensive tests cover various failure and success scenarios, ensuring that the code behaves as expected under different conditions.
