#!/bin/bash

# Variables
REGION="us-east-1" # Specify your region
SECURITY_GROUP_NAME="ec2-demo-group"
DESCRIPTION="Minimal security group for my EC2 instance for our S3 demo"

# Create a security group
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --region $REGION \
    --group-name $SECURITY_GROUP_NAME \
    --description "$DESCRIPTION" \
    --query 'GroupId' \
    --output text)

echo "Security group created with ID: $SECURITY_GROUP_ID"
