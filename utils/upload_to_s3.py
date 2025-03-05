from config import logger, S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
import os
import uuid
import boto3

def upload_to_s3(file_paths):
        """
        Upload multiple files to S3 and return their S3 URLs.

        Args:
            file_paths (list): List of local file paths to upload.

        Returns:
            list: List of S3 URLs for the uploaded files.
        """
        s3_urls = []
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )

            for local_file_path in file_paths:
                s3_file_key = f"{uuid.uuid4()}_{os.path.basename(local_file_path)}"
                # Upload the file
                s3_client.upload_file(local_file_path, S3_BUCKET_NAME, s3_file_key)

                # Generate the S3 URL and append it to the list
                s3_url = f"https://web-extension-screenshots.s3.{AWS_REGION}.amazonaws.com/{s3_file_key}"
                s3_urls.append(s3_url)

                logger.info(f"Uploaded file to S3: {s3_file_key}")

        except Exception as e:
            logger.error(f"Failed to upload files to S3: {e}")
            raise

        return s3_urls