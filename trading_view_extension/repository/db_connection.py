import psycopg2
from psycopg2.extras import RealDictCursor
from config import logger, DATABASE_URL

# Database connection details

class DBConnection:
    def __init__(self):
        self.connection = self.initialize_db_connection()

    def initialize_db_connection(self):
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


    def insert_job(self,job_data):
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
                        "agent": "model_a",
                        "status": "pending"
                    }
        """
        try:
            with self.connection.cursor() as cursor:
                query = """
                      INSERT INTO jobs (job_id, user_id, tab_id, websocket_id, agent, status, action_type, filenames, s3_urls, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, DEFAULT, DEFAULT)
            """
                cursor.execute(query, (
                job_data["job_id"],
                job_data["user_id"],
                job_data["tab_id"],
                job_data["websocket_id"],  # Optional
                job_data["agent"],  # Optional
                job_data["status"],
                job_data["action_type"],
                job_data["filenames"],  # Should be a list (TEXT[] in PostgreSQL)
                job_data["s3_urls"]     # Should be a list (TEXT[] in PostgreSQL)
            ))
                self.connection.commit()
                logger.info("Job inserted successfully.")
        except Exception as e:
            logger.info("Error inserting job:", e)


    def fetch_job(self, user_id, tab_id):
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
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
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
        
    def update_job_status(self, job_id, status):
        """
        Update the status of a job record in the jobs table.

        Args:
            connection: The PostgreSQL database connection object.
            job_id: The job_id of the job record to update.
            status: The new status value to set.
        """
        try:
            with self.connection.cursor() as cursor:
                query = """
                    UPDATE jobs
                    SET status = %s
                    WHERE job_id = %s
                """
                cursor.execute(query, (status, job_id))
                self.connection.commit()
                logger.info("Job status updated successfully.")
        except Exception as e:
            logger.info("Error updating job status:", e)

    def close_connection(self):
        """
        Close the PostgreSQL database connection.
        """
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed.")
        else:
            logger.info("No database connection to close.")
