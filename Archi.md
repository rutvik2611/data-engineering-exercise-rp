# Serverless Data Lake Architecture on AWS

## 1. Data Ingestion
- **Source:** OpenLibrary API
- **Service:** AWS Lambda
- **Trigger:** Amazon EventBridge
- **Role:** An AWS Lambda function is scheduled by EventBridge to periodically pull data from the OpenLibrary API. It extracts 'subject' data and writes the raw data to the `raw_data` directory in an S3 bucket.

## 2. Data Storage
- **Service:** Amazon S3
- **Bucket:** A centralized bucket for storing both raw and processed data.
- **Directories:**
  - `raw_data/`: Contains raw data files.
  - `processed_data/`: Contains cleaned and transformed data.

## 3. Data Processing
- **Service:** AWS Lambda
- **Trigger:** S3 Event Notification
- **Role:** A Lambda function is triggered when new files are uploaded to the `raw_data/` directory. It reads the raw files, performs data transformations (such as cleaning, normalization, and enrichment), and writes the processed data to the `processed_data/` directory within the same S3 bucket.

## 4. Data Transformation
- **Service:** AWS Glue (optional but recommended for complex transformations)
- **Role:** For more complex data transformations beyond Lambda's capabilities, AWS Glue can be used to run ETL jobs.
- **Function:** Define Glue ETL jobs to handle intricate data transformations and load the data into an S3 bucket or a data warehouse.

## 5. Data Analysis and Visualization
- **Service:** Amazon QuickSight
- **Role:** Connects to the `processed_data/` directory in S3.
- **Function:** Provides interactive dashboards and visualizations for deriving insights and business intelligence.

  **Alternative Tools:**
  - **Apache Superset:** An open-source alternative to QuickSight, offering robust visualization and dashboard features.
  - **Plotly:** For creating detailed static visualizations that can be downloaded and shared.

## 6. Monitoring and Logging
- **Service:** Amazon CloudWatch
- **Role:** Monitors Lambda functions and EventBridge schedules.
- **Function:** Captures logs and metrics, and sets up alarms for error notifications and performance monitoring.

## 7. Security and Access Control
- **Service:** AWS IAM
- **Role:** Manages permissions and access controls for Lambda functions, S3 buckets, and other services.
- **Function:** Ensures secure, least-privilege access to data and resources.


