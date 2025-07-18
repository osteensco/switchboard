#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Define variables
DIST_DIR="dist"
ZIP_FILE="lambda_package.zip"
PYTHON_FILES=("./src/executor.py" "./src/switchboard.py" "./src/tasks.py")

# 1. Create a clean distribution directory
echo "Creating a clean distribution directory..."
rm -rf $DIST_DIR
mkdir -p $DIST_DIR

# 2. Install Python dependencies
echo "Installing Python dependencies..."
pip install -r ../../sdk/py/requirements.txt -t $DIST_DIR

# 3. Copy Python files to the distribution directory
echo "Copying Python files..."
for file in "${PYTHON_FILES[@]}"; do
  cp "$file" "$DIST_DIR/"
done

# 4. Create the zip file for the Lambda function
echo "Creating zip file for Lambda..."
(cd $DIST_DIR && zip -r "../$ZIP_FILE" .)

# 5. Deploy with Terraform
echo "Deploying with Terraform..."
(cd terraform && terraform init && terraform apply -auto-approve)

echo "Deployment successful!"
