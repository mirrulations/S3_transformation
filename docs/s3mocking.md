# Mocking an S3 Bucket for AWS Lambda with Moto

## **Overview**
This guide demonstrates how to use **Moto** to mock an **S3 bucket** while using a lambda  function. Moto allows you to simulate AWS services locally, making it useful for unit testing without interacting with real AWS resources.

---

## **1. Install Dependencies**
Ensure you have `moto` and `boto3` installed in your Python environment.

```sh
pip install 'moto[all]' boto3 pytest
```
(You can also install specific services ie. pip install 'moto[s3,ec2]', etc.)

---

## **2. Lambda Function with S3 Operations**

This Lambda function interacts with S3: creating a bucket, uploading a file, and retrieving its content.

```python
import boto3
import json

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket_name = "my-mock-bucket"

    # Ensure bucket exists
    s3.create_bucket(Bucket=bucket_name)

    # Upload a file
    s3.put_object(Bucket=bucket_name, Key="test.txt", Body="ETL group is awesome!")

    # Retrieve the file
    response = s3.get_object(Bucket=bucket_name, Key="test.txt")
    content = response['Body'].read().decode('utf-8')

    return {
        'statusCode': 200,
        'body': json.dumps({'content': content})
    }
```

---

## **3. Unit Test with Moto**

Using `pytest` and `Moto`, we mock an S3 bucket to test the Lambda function.

```python
import boto3
import json
import pytest
from moto import mock_aws
import os

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for Moto"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@mock_aws
def test_lambda_handler(aws_credentials):
    """Test the Lambda function with a mocked S3 bucket"""
    
    # Setup mock S3
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="my-mock-bucket")

    # Call the Lambda function
    response = lambda_handler({}, {})

    # Validate the response
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["content"] == "ETL group is awesome!"
```

---

## **4. Key Takeaways**
- **Moto intercepts AWS calls**, so no actual S3 bucket is needed.
- **Use `@mock_aws`** to simulate S3 operations.
- **Manually create the bucket in the test** if your function assumes it already exists.
- **Mock AWS credentials** to avoid real API calls.

This setup allows you to **test S3-dependent Lambda functions** locally without needing real AWS resources.
