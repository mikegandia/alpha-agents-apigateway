from config import logger
from utils.upload_to_s3 import upload_to_s3
from trading_view_extension.repository.db_connection import DBConnection
from trading_view_extension.managers.analysis_task_manager import AnalysisTaskManager

class AnalysisRouter:
    def __init__(self, db:DBConnection, task_manager:AnalysisTaskManager):
        """
        Initialize AnalysisRouter with a DBConnection instance.
        """
        self.db = db
        self.task_manager = task_manager


    async def create_analysis(self, data):
        """
        Create a new analysis job that may contain multiple file_paths.

        Data should contain:
        - 'file_paths': list of local file paths
        - 'filenames': list of original file names (optional, just for reference)
        - other metadata like 'agent', 'tab_id', 'user_id'...
        """
        try:
            # Upload all file paths to S3 and get the S3 URLs
            s3_urls = upload_to_s3(data.get('file_paths', []))
            # Add S3 URLs to data
            data['s3_urls'] = s3_urls
            self.db.insert_job(data)  # Use DBConnection instance
            await self.task_manager.publish_analysis_task(**data)

        except Exception as e:
            logger.error(f"Failed to create analysis job: {e}")
            raise
