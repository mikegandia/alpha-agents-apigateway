import asyncio
import json
from config import logger, output_tasks_queue
from trading_view_extension.queue.sqs_queue_consumer import SqsQueueConsumer
from trading_view_extension.managers.session_manager import SessionManager

class ResponseWorker:
    """
    Consumes messages from the "analysis-completed" queue and processes them.
    Specifically, it fetches the websocket connection from SessionManager and
    sends the processed job data back to that websocket.
    """
    def __init__(
        self,
        queue_consumer: SqsQueueConsumer,
        session_manager: SessionManager,  # Accept SessionManager instance
        job_repository=None,   # Optional: if you need to interact with the database
        real_time_manager=None # Optional: if you need to push updates to users
    ):
        self.queue_consumer = queue_consumer
        self.job_repository = job_repository
        self.real_time_manager = real_time_manager
        self.session_manager = session_manager
        logger.info("ResponseWorker initialized")

    async def start_listening(self) -> None:
        """
        Continuously fetch messages from the "analysis-completed" SQS queue and process them.
        """
        queue_url = output_tasks_queue.url  # Fetch the output queue URL from config
        logger.info(f"ResponseWorker listening on {queue_url}")
        while True:
            try:
                messages = await self.queue_consumer.receive_messages(queue_url)
                logger.debug(f"Received {len(messages)} jobs in output queue")
                for message in messages:
                    try:
                        await self.process_completed_task(message)
                    except Exception as exc:
                        logger.exception(f"Failed to process message {message.get('MessageId')}: {exc}")
                    finally:
                        # Always delete the message to avoid infinite re-delivery
                        await self.queue_consumer.delete_message(queue_url, message)
            except Exception as e:
                logger.exception(f"Error while fetching messages: {e}")
            await asyncio.sleep(1)  # Adjust the sleep duration as needed

    async def process_completed_task(self, message: dict) -> None:
        """
        Processes a single completed analysis task message:
          1) Parses the JSON body.
          2) Sends the result via WebSocket if websocket_id is provided and valid.
        """
        logger.info(f"Processing completed task message: {message.get('MessageId')}")
        try:
            data = json.loads(message.get("Body", "{}"))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message {message.get('MessageId')}: {e}")
            return

        await self.manage_processed_job(data)

    async def manage_processed_job(self, data: dict) -> None:
        """
        Fetches the websocket connection (using websocket_id from data)
        and sends the processed job data back to that websocket.
        """
        websocket_id = data.get("websocket_id")
        if not websocket_id:
            logger.warning("No 'websocket_id' found in the data; cannot send response.")
            return

        ws_connection = self.session_manager.get_websocket(websocket_id)
        if not ws_connection:
            logger.warning(f"No active WebSocket connection found for ID: {websocket_id}")
            return

        try:
            # Send the entire processed data to the client
            await ws_connection.send(json.dumps(data))
            logger.info(f"Sent processed job details to WebSocket {websocket_id}")
        except Exception as e:
            logger.exception(f"Failed to send data to WebSocket {websocket_id}: {e}")
