"""
File cleanup utilities for managing downloaded files.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def cleanup_file_after_download(file_path: str) -> bool:
    """
    Clean up a file after it has been downloaded.
    
    Args:
        file_path: Path to the file to clean up
        
    Returns:
        bool: True if file was successfully deleted, False otherwise
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file after download: {file_path}")
            return True
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")
    return False


def schedule_file_cleanup(file_path: str, delay_seconds: int = 5) -> None:
    """
    Schedule file cleanup after a delay.
    
    Args:
        file_path: Path to the file to clean up
        delay_seconds: Delay before cleanup in seconds
    """
    import threading
    import time
    
    def delayed_cleanup():
        time.sleep(delay_seconds)
        cleanup_file_after_download(file_path)
    
    # Start cleanup in background thread
    cleanup_thread = threading.Thread(target=delayed_cleanup, daemon=True)
    cleanup_thread.start()
    logger.info(f"Scheduled cleanup for {file_path} in {delay_seconds} seconds")
