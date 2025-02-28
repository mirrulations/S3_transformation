#!/bin/bash

# Install Git
sudo yum update -y
sudo yum install -y git

# Clone the repository
REPO_URL="https://github.com/elon-shmusk/transformation_trigger.git"
git clone $REPO_URL

# Navigate into the repository directory
REPO_NAME="transformation_trigger"
cd $REPO_NAME

# Navigate to the move directory
cd S3/

# Create and activate a virtual environment
sudo yum install -y python3
python3 -m venv .venv
source .venv/bin/activate

# Install the requirements
pip install boto3

# Run the script
python3 move.py