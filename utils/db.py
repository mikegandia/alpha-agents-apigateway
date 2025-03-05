import psycopg2
from psycopg2.extras import RealDictCursor
from config import logger

# Database connection details
DATABASE_URL = "postgresql://postgres_admin:TLYX0mxibUR1yakz@database-1.c7mcu4qq0ofd.us-east-1.rds.amazonaws.com:5432/ATS"

def initialize_db_connection():
    """
    Initialize and return the PostgreSQL database connection object.
    """
    try:
        connection = psycopg2.connect(DATABASE_URL)
        logger.info("Database connection initialized successfully.")
        return connection
    except Exception as e:
        logger.info("Error initializing database connection:", e)
        return None


def insert_job(connection, job_data):
    """
    Insert a job record into the jobs table.
    
    Args:
        connection: The PostgreSQL database connection object.
        job_data: A dictionary containing the job details.
                  Example:
                  {
                      "job_id": "123",
                      "user_id": "user1",
                      "tab_id": "tab1",
                      "websocket_id": "ws123",
                      "model_choice": "model_a",
                      "status": "pending"
                  }
    """
    try:
        with connection.cursor() as cursor:
            query = """
                INSERT INTO jobs (job_id, user_id, tab_id, websocket_id, model_choice, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                job_data["job_id"],
                job_data["user_id"],
                job_data["tab_id"],
                job_data["websocket_id"],
                job_data["model_choice"],
                job_data["status"]
            ))
            connection.commit()
            logger.info("Job inserted successfully.")
    except Exception as e:
        logger.info("Error inserting job:", e)


def fetch_job(connection, user_id, tab_id):
    """
    Fetch a job record from the jobs table based on user_id and tab_id.

    Args:
        connection: The PostgreSQL database connection object.
        user_id: The user_id to filter by.
        tab_id: The tab_id to filter by.

    Returns:
        The fetched job record as a dictionary, or None if no record is found.
    """
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT * FROM jobs
                WHERE user_id = %s AND tab_id = %s
            """
            cursor.execute(query, (user_id, tab_id))
            result = cursor.fetchone()
            return result
    except Exception as e:
        logger.info("Error fetching job:", e)
        return None
