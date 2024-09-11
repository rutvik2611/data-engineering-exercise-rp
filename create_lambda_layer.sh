#!/bin/bash # not working

# SSH connection details
SSH_USER="root"
SSH_HOST="rutvik2611.com"
REMOTE_DIR="/app/development"
REQUIREMENTS_TXT="requirements.txt"
ZIP_FILE="python_env.zip"
S3_BUCKET="s3://rp-data-engg-rp/lambda-layer/"

# Define the content for requirements.txt based on the Pipfile
REQUIREMENTS_CONTENT=$(cat <<EOF
requests
sqlalchemy
boto3
python-dotenv
sqlalchemy-cockroachdb
psycopg2-binary
EOF
)

# Create requirements.txt file in the current directory
echo "$REQUIREMENTS_CONTENT" > "$REQUIREMENTS_TXT"

# Copy requirements.txt to remote directory
scp "$REQUIREMENTS_TXT" "${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/"

# Commands to run on remote machine
REMOTE_COMMANDS=$(cat <<EOF
    cd $REMOTE_DIR
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    zip -r python_env.zip venv
EOF
)

# Execute remote commands
ssh "${SSH_USER}@${SSH_HOST}" "$REMOTE_COMMANDS"

# Copy the ZIP file back to the current directory
scp "${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/python_env.zip" .

# Clean up the remote directory
ssh "${SSH_USER}@${SSH_HOST}" "rm -rf ${REMOTE_DIR}/venv ${REMOTE_DIR}/python_env.zip"

# Optionally, remove local requirements.txt file
rm "$REQUIREMENTS_TXT"

# Upload the ZIP file to S3, replacing if it already exists
aws s3 cp "$ZIP_FILE" "$S3_BUCKET" --region us-west-2 --acl bucket-owner-full-control --no-progress

# Clean up the local ZIP file
rm "$ZIP_FILE"

echo "Process completed successfully."
