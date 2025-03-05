# trading_view_extension/analysis_router/analysis_router.py

import logging
import asyncio
from utils.db import initialize_db_connection, fetch_job, insert_job
from trading_view_extension.websocket_manager.websocket_manager import WebSocketManager
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AnalysisRouter:
    def __init__(self):
        logging.info("AnalysisRouter initialized.")
        self.db_connection = initialize_db_connection()
        self.wsm = WebSocketManager()

    async def upload_images_to_s3(self, file_path: str, metadata: dict):
        """
        Simulates uploading images to S3 and stores metadata in PostgreSQL.

        Args:
            file_path (str): Path to the image file to be uploaded.
            metadata (dict): Metadata for the image upload. Example:
                {
                    "job_id": "123",
                    "user_id": "user1",
                    "tab_id": "tab1",
                    "websocket_id": "ws123",
                    "model_choice": "model_a",
                    "status": "pending"
                }
        """
        
        data = {
            "job_id": str(random.randint(1000,9999)),
            "user_id": metadata["user_id"],
            "tab_id": metadata["tab_id"],
            "websocket_id": id(metadata["websocket"]),
            "model_choice": metadata["agent"],
            "status": "PENDING"
        }

        self.wsm.add_connection( data["websocket_id"],metadata["websocket"])

        logging.info(f"metadata: {data}")

        # Simulate image upload (dummy implementation)
        # await asyncio.sleep(1)  # Simulating an async operation
        logging.info(f"File uploaded to S3: {file_path}")

        # Insert job metadata into PostgreSQL
        try:
            insert_job(self.db_connection,data)
            # await asyncio.sleep(2)  # Simulating an async operation
            await self.fetch_job_metadata(data["user_id"], data["tab_id"])
        except Exception as e:
            logging.error(f"Error inserting job metadata into the database: {e}")

    async def fetch_job_metadata(self, user_id: str, tab_id: str):
        """
        Fetch job metadata from the database based on user_id and tab_id.

        Args:
            user_id (str): User ID for filtering the job.
            tab_id (str): Tab ID for filtering the job.

        Returns:
            dict: Job metadata if found, otherwise None.
        """
        try:
            job_metadata = fetch_job(self.db_connection,user_id, tab_id)
            if job_metadata:
                logging.info(f"Job metadata fetched: {job_metadata}")
                logging.info(f"Websocket ID: {job_metadata.get('websocket_id')}")
                websocket = job_metadata.get("websocket_id")
                if websocket:
                    websocket= self.wsm.get_connection(websocket)
                    logging.info(f"Websocket: {websocket}")
                    await websocket.send(f"Websocket fetched for tab_id: {tab_id} and user_id: {user_id}")
            else:
                logging.info(f"No job found for user_id: {user_id}, tab_id: {tab_id}")
            return job_metadata
        except Exception as e:
            logging.error(f"Error fetching job metadata from the database: {e}")
            return None
