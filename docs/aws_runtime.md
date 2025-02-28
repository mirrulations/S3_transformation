# AWS S3 Data Copying and Deletion: A Technical Report

This report explains how data copying within Amazon S3 is handled entirely within AWS infrastructure without involving your local machine. It also details the asymptotic runtime for copying and deleting objects within the same S3 bucket, considering both small (less than 5 GB) and large objects (greater than 5 GB) that require multipart copying.

## 1. Server-Side Copying in AWS

When you perform a copy operation on an object within an S3 bucket using the `CopyObject` API, the operation is executed entirely within AWS servers. This means:

- **No local downloading:** The data is not transferred to your device at any point. Instead, the copying process is performed on the AWS backend.
- **Efficient operation:** Since the operation is handled server-side, it is optimized for performance by eliminating the overhead of downloading and re-uploading the object.

This approach leverages the internal AWS network and metadata operations to efficiently duplicate objects within the same bucket.

For more details, refer to the AWS documentation on the [CopyObject](https://docs.aws.amazon.com/AmazonS3/latest/userguide/copy-object.html?utm_source) operation. :contentReference[oaicite:0]{index=0}

## 2. Asymptotic Run Time Analysis

### 2.1. Files Smaller Than 5 GB

For objects smaller than 5 GB, a single `CopyObject` operation is used:
- **Copy Operation:** This operation is effectively **O(1)**, as it is handled as a metadata update without scaling with the object size.
- **Delete Operation:** Deleting an object is also **O(1)**.

Thus, the overall time complexity for moving an object (copying and then deleting) is:
\[
O(1) + O(1) = O(1)
\]
This means that for a single object, regardless of its size (under 5 GB), the operations complete in constant time.

### 2.2. Files Larger Than 5 GB

For objects larger than 5 GB, AWS recommends using a multipart copy operation. This process involves:
- Dividing the object into smaller parts.
- Copying each part individually, which can be executed in parallel.

While each individual part copy operation is **O(1)**, the overall time for the multipart copy depends on:
- The number of parts the file is divided into.
- The parallelization and network performance between AWS servers.

Assuming the file is divided into \( n \) parts, the overall complexity can be viewed as:
\[
O(n)
\]
However, since \( n \) is determined by the fixed part size (and thus indirectly by the object size), the runtime increases linearly with the number of parts.

For further details on multipart copy, refer to the AWS documentation on [Multipart Upload and Copy](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html?utm_source). :contentReference[oaicite:1]{index=1}

## 3. Conclusion

- **Server-Side Efficiency:** When copying an object within the same S3 bucket, the entire operation is performed within the AWS infrastructure, without any data being transferred to your local machine.
- **Asymptotic Complexity:**
  - **Files < 5 GB:** Copying and deleting an object both have a constant time complexity, \( O(1) \).
  - **Files > 5 GB:** Multipart copying scales linearly with the number of parts, leading to an overall complexity of \( O(n) \), where \( n \) is the number of parts.
  
These optimizations ensure that AWS S3 remains efficient even when handling large-scale data operations.

## Sources

- AWS S3 CopyObject Documentation: [docs.aws.amazon.com](https://docs.aws.amazon.com/AmazonS3/latest/userguide/copy-object.html?utm_source) :contentReference[oaicite:2]{index=2}  
- AWS S3 Multipart Upload Overview: [docs.aws.amazon.com](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html?utm_source) :contentReference[oaicite:3]{index=3}

## Rough Draft of Approximated Runtime on Mirrulations Bucket
 - For 1.4 GBs of data it took 23.1 minutes
 - Calculating for 2.2 TBs it would take approximatley 25.2 days
   - 23.1 minutes/1.4 GBs = 16.5 minutes per GB
   - 2,200 GBs(2.2 TBS) x 16.5 minutes = 36,300 minutes
   - 36,300/60 = 605 hours, 605/24 = 25.2 days
