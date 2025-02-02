import asyncio
from utils.websocket import WebSocketServer
from trading_view_extension.routers.analysis_router import AnalysisRouter
from trading_view_extension.repository.db_connection import DBConnection
from trading_view_extension.managers.analysis_task_manager import AnalysisTaskManager
from trading_view_extension.queue.sqs_queue_publisher import SQSQueuePublisher
from trading_view_extension.workers.response_worker import ResponseWorker
from trading_view_extension.queue.sqs_queue_consumer import SqsQueueConsumer
from trading_view_extension.managers.session_manager import SessionManager
from config import logger  # Ensure logger is imported from config.py

async def main():
    # Initialize all dependencies
    db = DBConnection()
    iqp = SQSQueuePublisher()
    atm = AnalysisTaskManager(iqp)
    sqs_consumer = SqsQueueConsumer()
    session_manager = SessionManager()  # Initialize SessionManager

    analysis_router = AnalysisRouter(db, atm)
    server = WebSocketServer(analysis_router, session_manager)  # Pass session_manager

    # Initialize Workers
    response_worker = ResponseWorker(queue_consumer=sqs_consumer, session_manager=session_manager)

    server_task = asyncio.create_task(server.run())
    response_worker_task = asyncio.create_task(response_worker.start_listening())
 
    # Run all tasks concurrently until one raises an exception
    done, pending = await asyncio.wait(
        [server_task, response_worker_task],
        return_when=asyncio.FIRST_EXCEPTION
    )

    # Handle task completion or exceptions
    for task in done:
        if task.exception():
            logger.error(f"Task failed: {task.exception()}")
            # Optionally, cancel other pending tasks
            for pending_task in pending:
                pending_task.cancel()
            raise task.exception()

    # Close DB connections if necessary
    db.close_connection()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down due to KeyboardInterrupt")
    except Exception as e:
        logger.error(f"Shutting down due to error: {e}")
