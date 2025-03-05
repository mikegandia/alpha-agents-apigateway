import os
import logging
from dotenv import load_dotenv
import boto3
from dataclasses import dataclass

# Load environment variables from the .env file
load_dotenv()

# --------------------------
# General Configuration
# --------------------------
PORT = int(os.getenv("PORT", 8080))
DATABASE_URL = os.getenv("DATABASE_URL")

# --------------------------
# Logging Configuration
# --------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_FILE = os.getenv("LOG_FILE", "trading_view_extension.log")

# Configure logging for the application
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),  # Log to file
        logging.StreamHandler(),        # Log to console
    ],
)
logger = logging.getLogger(__name__)

# --------------------------
# WebSocket host and port
# --------------------------
WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST", "localhost")
WEBSOCKET_PORT = int(os.getenv("PORT", 8080))

# --------------------------
# Directory for uploaded files
# --------------------------
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

# --------------------------
# AWS Configuration
# --------------------------
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize AWS clients
sqs_client = boto3.client(
    'sqs',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# --------------------------
# Data Classes for AWS SQS Queues
# --------------------------
@dataclass
class SQSQueue:
    name: str
    url: str
    arn: str
    client: boto3.client

# Initialize separate SQSQueue objects
input_tasks_queue = SQSQueue(
    name=os.getenv("SQS_INPUT_QUEUE_NAME"),
    url=os.getenv("SQS_INPUT_QUEUE_URL"),
    arn=os.getenv("SQS_INPUT_QUEUE_ARN"),
    client=sqs_client
)

output_tasks_queue = SQSQueue(
    name=os.getenv("SQS_OUTPUT_QUEUE_NAME"),
    url=os.getenv("SQS_OUTPUT_QUEUE_URL"),
    arn=os.getenv("SQS_OUTPUT_QUEUE_ARN"),
    client=sqs_client
)

# --------------------------
# AWS S3 Configuration
# --------------------------
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# # --------------------------
# # AWS RDS Configuration
# # --------------------------
# DATABASE_URL = "postgresql://postgres:2012@localhost:5432/postgres"
DATABASE_URL = "postgresql://postgres_admin:TLYX0mxibUR1yakz@database-1.c7mcu4qq0ofd.us-east-1.rds.amazonaws.com:5432/ATS"
# RDS_CONFIG = {
#     "endpoint": os.getenv("RDS_ENDPOINT"),
#     "port": int(os.getenv("RDS_PORT", 5432)),
#     "db_name": os.getenv("RDS_DB_NAME"),
#     "username": os.getenv("RDS_USERNAME"),
#     "password": os.getenv("RDS_PASSWORD"),
# }

# # --------------------------
# # Sandbox Configuration
# # --------------------------
# SANDBOX_CONFIG = {
#     "auth_token": os.getenv("SANDBOX_AUTH_TOKEN"),
#     "account_id": os.getenv("SANDBOX_ACCOUNT_ID"),
#     "url": os.getenv("SANDBOX_URL"),
# }

# # --------------------------
# # PostgreSQL Connection Pool Setup
# # --------------------------
# connection_pool = None

# try:
#     connection_pool = psycopg2.pool.SimpleConnectionPool(
#         minconn=1,  # Minimum number of connections to maintain in the pool
#         maxconn=10,  # Maximum number of connections the pool can open (adjust based on app needs)
#         dsn=DATABASE_URL,  # Database connection string loaded from the environment variable
#     )
#     if connection_pool:
#         logger.info("Database connection pool created successfully.")
# except InvalidPassword as e:
#     logger.error("Invalid password for database connection: Check credentials in DATABASE_URL.")
#     connection_pool = None
#     raise e
# except InsufficientPrivilege as e:
#     logger.error("Insufficient privileges to access the database: Ensure the user has proper roles.")
#     connection_pool = None
#     raise e
# except OperationalError as e:
#     logger.error(f"Operational error during connection pool setup: {e}")
#     connection_pool = None
#     raise e
# except InterfaceError as e:
#     logger.error(f"Interface error during connection pool setup: {e}")
#     connection_pool = None
#     raise e
# except Exception as e:
#     logger.error(f"Unexpected error while setting up connection pool: {e}")
#     connection_pool = None
#     raise e

# # --------------------------
# # Database Connection Functions
# # --------------------------

# def get_db_connection():
#     """
#     Retrieves a database connection from the pool.

#     Returns:
#         psycopg2.extensions.connection: A database connection object.

#     Raises:
#         ConnectionDoesNotExist: If there are no available connections in the pool.
#         InterfaceError: If there is an error with the database interface.
#         OperationalError: For operational issues like server unavailability.
#         Exception: For any other general error during connection retrieval.
#     """
#     if connection_pool is None:
#         logger.error("Connection pool is not available.")
#         raise RuntimeError("Database connection pool has not been initialized.")

#     try:
#         connection = connection_pool.getconn()
#         if connection:
#             logger.info("Successfully retrieved a connection from the pool.")
#         return connection
#     except ConnectionDoesNotExist as e:
#         logger.error("No available connections in the pool: Ensure proper pool limits.")
#         raise e
#     except InterfaceError as e:
#         logger.error("Interface error while acquiring connection from pool.")
#         raise e
#     except OperationalError as e:
#         logger.error(f"Operational error while acquiring connection: {e}")
#         raise e
#     except Exception as e:
#         logger.error(f"Unexpected error while acquiring connection: {e}")
#         raise e

# def release_db_connection(connection):
#     """
#     Releases a database connection back to the pool.

#     Args:
#         connection (psycopg2.extensions.connection): A database connection object.

#     Raises:
#         InterfaceError: If there is an issue releasing the connection.
#         Exception: For any other general error during release.
#     """
#     if connection and connection_pool:
#         try:
#             connection_pool.putconn(connection)
#             logger.info("Connection successfully released back to the pool.")
#         except InterfaceError as e:
#             logger.error("Interface error while releasing connection back to the pool.")
#             raise e
#         except Exception as e:
#             logger.error(f"Unexpected error while releasing connection: {e}")
#             raise e
#     else:
#         logger.warning("No valid connection or connection pool to release.")

# def close_all_connections():
#     """
#     Closes all database connections in the pool.

#     Raises:
#         OperationalError: If there is an issue closing the connections.
#         Exception: For any other general error during closure.
#     """
#     if connection_pool:
#         try:
#             connection_pool.closeall()
#             logger.info("All database connections have been closed successfully.")
#         except OperationalError as e:
#             logger.error(f"Operational error while closing all connections: {e}")
#             raise e
#         except Exception as e:
#             logger.error(f"Unexpected error while closing connections: {e}")
#             raise e
#     else:
#         logger.warning("No connection pool found to close.")

# # Register the shutdown handler to close all connections when the app terminates
# atexit.register(close_all_connections)

# # --------------------------
# # Validate Critical Configurations
# # --------------------------
# def validate_config():
#     required_vars = [
#         "DATABASE_URL",
#         "AWS_ACCESS_KEY_ID",
#         "AWS_SECRET_ACCESS_KEY",
#         "SQS_INPUT_QUEUE_URL",
#         "SQS_OUTPUT_QUEUE_URL",
#         "S3_BUCKET_NAME",
#         "RDS_ENDPOINT",
#         "RDS_DB_NAME",
#         "RDS_USERNAME",
#         "RDS_PASSWORD",
#     ]

#     missing_vars = [var for var in required_vars if not os.getenv(var)]

#     if missing_vars:
#         logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
#         raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
#     else:
#         logger.info("All required environment variables are set.")

# # Validate configurations at startup
# validate_config()