#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Define variables
DIST_DIR="dist"
ZIP_FILE="lambda_package.zip"
PYTHON_FILES=("./src/executor.py" "./src/workflow.py" "./src/tasks.py")

# 1. Create a clean distribution directory
echo "Creating a clean distribution directory..."
rm -rf $DIST_DIR
mkdir -p $DIST_DIR

# 2. Install Python dependencies
echo "Installing Python dependencies..."
pip install -r ../../sdk/py/requirements.txt -t $DIST_DIR
# clean up unneeded stuff
find "$DIST_DIR" -type d -name "*.dist-info" -exec rm -rf {} +
find "$DIST_DIR" -type d -name "*.egg-info" -exec rm -rf {} +
find "$DIST_DIR" -type d -name "__pycache__" -exec rm -rf {} + 

# 3. Copy Python files to the distribution directory
echo "Copying Python files..."
mkdir -p $DIST_DIR/src
cp -r ../../sdk/py/src/switchboard $DIST_DIR
for file in "${PYTHON_FILES[@]}"; do
  cp "$file" "$DIST_DIR/src/"
done

# 4. Create the zip file for the Lambda function
echo "Creating zip file for Lambda..."
(cd $DIST_DIR && zip -r "../$ZIP_FILE" .)
touch "$ZIP_FILE"

echo "Switchboard deployment package created."
#
# # 5. Deploy with Terraform
# echo "Deploying with Terraform..."
# (cd terraform && terraform init && terraform validate && terraform apply)
#
# echo "Deployment successful! Run the trigger_workflow.py script to test it out."
