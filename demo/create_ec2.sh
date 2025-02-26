#!/bin/bash

# Variables
REGION="us-east-1" # Specify your region
AMI_ID="ami-053a45fff0a704a47" # Amazon Linux AMI ID
INSTANCE_TYPE="t2.micro" # Specify your instance type
USER_DATA_FILE="./setup.sh" # Path to your user data script file
SECURITY_GROUP_ID="sg-0fa24898b3bf632fb" # Your existing security group ID
IAM_ROLE_NAME="S3DemoRole" # Your IAM role name

# Create EC2 instance with IAM role
aws ec2 run-instances \
    --region $REGION \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --security-group-ids $SECURITY_GROUP_ID \
    --user-data file://$USER_DATA_FILE \
    --iam-instance-profile Name=$IAM_ROLE_NAME \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=YourInstanceName}]'

echo "EC2 instance created successfully with security group $SECURITY_GROUP_ID and IAM role $IAM_ROLE_NAME"
