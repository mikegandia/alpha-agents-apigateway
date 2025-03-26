import asyncio
import websockets
import json
import os
import struct
import shutil
from config import WEBSOCKET_HOST, WEBSOCKET_PORT, logger
from trading_view_extension.routers.analysis_router import AnalysisRouter
from trading_view_extension.managers.session_manager import SessionManager
import uuid

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

connected_users = {}

class WebSocketServer:
    def __init__(self, analysis_router : AnalysisRouter , session_manager: SessionManager):
        """
        Initializes the WebSocketServer with an AnalysisRouter instance.
        """
        self.analysis_router = analysis_router
        self.ssm = session_manager

    async def handle_connection(self, websocket, path=None):
        """
        Handles a new WebSocket connection, processes incoming messages, and manages cleanup.
        """
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    await self.process_binary_message(websocket, message)
                else:
                    await self.process_text_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Error handling connection: {e}")
        # finally:
            await self.cleanup(websocket)

    async def process_binary_message(self, websocket, message):
        """
        Process a single binary message that can contain multiple images.
        We will parse each image, but only after parsing them all, we create a single 'job' that
        references all images at once.
        """
        offset = 0
        total_length = len(message)

        # Store data for a single "job"
        images_file_paths = []
        images_filenames = []
        # We might also want to store a "common" metadata dictionary, e.g., user_id, agent, etc.
        # The assumption here is that each chunk has identical user_id, agent, tab_id, etc.
        # You can adapt this to handle differences if needed.
        common_metadata = {}
        user_id = None  # track userId from the first chunk
        tab_id = None   # track tabId from the first chunk
        agent = None    # track agent from the first chunk
        user_instructions = None
        email_id = None
        agent_query = None
        prompt = None
        message_id = None

        while offset < total_length:
            # 1) We must have 4 bytes for metadata length
            if offset + 4 > total_length:
                logger.warning("Invalid message: too short to read the 4-byte metadata length.")
                await websocket.send("Error: Invalid message format (no metadata length).")
                break

            # 2) Read metadata length (big-endian)
            metadata_length = struct.unpack('>I', message[offset : offset + 4])[0]
            offset += 4

            # 3) Check we have enough bytes for metadata
            if offset + metadata_length > total_length:
                logger.warning("Invalid message: incomplete metadata based on metadata_length.")
                await websocket.send("Error: Incomplete metadata.")
                break

            # 4) Parse metadata JSON
            metadata_bytes = message[offset : offset + metadata_length]
            offset += metadata_length
            try:
                metadata = json.loads(metadata_bytes.decode('utf-8'))
            except json.JSONDecodeError:
                logger.warning("Invalid metadata JSON.")
                await websocket.send("Error: Invalid metadata JSON.")
                break

            # If desired, capture 'common' fields from the first chunk
            if user_id is None:
                user_id = metadata.get("user_id")
                tab_id = metadata.get("tab_id")
                agent = metadata.get("agent")
                asset = metadata.get("asset")
                user_instructions = metadata.get("user_instructions")
                email_id = metadata.get("email_id")
                prompt = metadata.get("prompt")
                agent_query = metadata.get("agent_query")
                message_id = metadata.get("message_id", "")
                # Optionally store them in a common_metadata dictionary if you want
                common_metadata = {
                    "agent": agent,
                    "tab_id": tab_id,
                    "user_id": user_id,
                    "action_type": metadata.get("action_type", "analysis"),
                }

            # 5) Make sure we have blob_size
            blob_size = metadata.get("blob_size")
            if blob_size is None:
                logger.warning("No 'blob_size' provided in metadata; cannot parse multiple images reliably.")
                await websocket.send("Error: 'blob_size' is required to parse multiple images.")
                break

            # 6) Check if we have enough bytes for this image
            if offset + blob_size > total_length:
                logger.warning("Invalid message: not enough bytes for the declared blob_size.")
                await websocket.send("Error: Incomplete image data (blob_size mismatch).")
                break

            # 7) Extract binary data for this image
            binary_data = message[offset : offset + blob_size]
            offset += blob_size

            # 8) Save the file
            file_path = self.save_file(metadata, binary_data)

            # Collect for single-job usage
            images_file_paths.append(file_path)
            filename = metadata.get("filename", "unknown")
            
            if filename is "unknown":
                images_filenames = []
            else:
                images_filenames.append(metadata.get("filename", "unknown"))

            # We do NOT call create_analysis() here. We'll do it after the loop.

        # ------------------------------------------------------
        # AFTER we've parsed all images, create a single job/record
        # that references all images
        # ------------------------------------------------------
        if images_file_paths:
            # For example, we can call a new method like create_analysis_batch()
            # or reuse create_analysis with a custom approach. Let's show a new method:

            try:
                # Build a dictionary representing the "job" or "analysis" that includes multiple images
                job_id = metadata.get("job_id")
                status = metadata.get("status", "PENDING")
                if job_id is None:
                    job_id = str(uuid.uuid4())
                    chat = False
                else:
                    chat = True
                job_data = {
                    "asset": asset,
                    "agent": agent,
                    "tab_id": tab_id,
                    "user_id": user_id,
                    "action_type": common_metadata.get("action_type"),
                    "job_id": job_id,  # will be generated
                    "status": "PENDING",
                    "websocket_id": id(websocket),
                    "is_chat": chat,
                    "user_instructions": user_instructions,
                    "email_id": email_id,
                    "agent_query": agent_query,
                    "prompt": prompt,
                    "message_id": message_id,
                    "filenames": images_filenames,       # array of just the names
                    "file_paths": images_file_paths,     # array of actual saved paths
                    # you can add more fields as desired
                }

                # Example: Suppose your analysis_router has a method create_analysis_batch
                # that expects a dictionary with "job_data" containing multiple images.
                # If you only have create_analysis, you can extend it or create a new one.
                self.ssm.register_websocket(str(id(websocket)),websocket)
                await self.analysis_router.create_analysis(job_data)
                # Send a single response to confirm the entire batch was processed
                await websocket.send(json.dumps({
                    "message": "Server received images and started processing",
                    "job_id": job_data["job_id"],
                    "asset": asset,
                    "agent": agent,
                }))
            except Exception as e:
                logger.error(f"Failed to process multiple images for user={user_id}: {e}")
                await websocket.send("Error: Failed to process multiple files in batch.")

    async def process_text_message(self, websocket, message):
        """
        Processes text messages, typically containing user identification or "handshake" data.
        """
        try:
            data = json.loads(message)
            logger.info(
                f"New connection established for userId: {data.get('user_id', 'unknown')} "
                f"with tabId: {data.get('tab_id', 'unknown')}"
            )
            await websocket.send("Connection established.")
        except json.JSONDecodeError:
            logger.warning(f"Invalid text message: {message}")
            await websocket.send("Error: Invalid JSON format.")

    def save_file(self, metadata, binary_data):
        """
        Saves the binary file to the designated upload directory based on metadata.
        """
        user_id = metadata.get("user_id", "unknown")
        filename = metadata.get("filename", "unknown")
        tab_id = metadata.get("tab_id", "unknown")

        # Create user directory
        user_dir = os.path.join(UPLOAD_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        # logger.info(f"Using user directory: {user_dir}")

        # Create a "stock" subdirectory from the filename (arbitrary logic)
        stock_name = "UnknownStock"
        if "_" in filename:
            stock_name = filename.split("_")[0]
        stock_dir = os.path.join(user_dir, stock_name)
        os.makedirs(stock_dir, exist_ok=True)
        # logger.info(f"Using stock directory: {stock_dir}")

        # Construct final file path
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(stock_dir, f"{tab_id}_{safe_filename}")

        with open(file_path, "wb") as f:
            f.write(binary_data)

        return file_path

    async def cleanup(self, websocket):
        """
        Cleans up resources and deletes the user's upload directory upon disconnection.
        """
        if websocket in connected_users:
            user_id = connected_users[websocket]
            user_dir = os.path.join(UPLOAD_DIR, str(user_id))
            if os.path.exists(user_dir):
                try:
                    shutil.rmtree(user_dir)
                    logger.info(f"Deleted user directory: {user_dir}")
                except Exception as e:
                    logger.error(f"Error deleting user directory {user_dir}: {e}")
            del connected_users[websocket]

    async def run(self):
        """
        Starts the WebSocket server and listens for incoming connections indefinitely.
        """
        async with websockets.serve(self.handle_connection, WEBSOCKET_HOST, WEBSOCKET_PORT):
            logger.info(f"WebSocket server running on ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
            await asyncio.Future()  # Run forever


