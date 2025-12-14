import asyncio
import os
from datetime import datetime
from pathlib import Path
from backend.database import SessionLocal
from backend.models import Secret
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_expired_secrets():
    """Background task to clean up expired secrets and their files"""
    while True:
        try:
            db = SessionLocal()
            
            # Find all expired secrets
            secrets = db.query(Secret).all()
            deleted_count = 0
            
            for secret in secrets:
                if secret.is_expired():
                    # Delete associated file if exists
                    if secret.file_path:
                        file_path = Path(secret.file_path)
                        if file_path.exists():
                            try:
                                os.remove(file_path)
                                logger.info(f"Deleted file: {file_path}")
                            except Exception as e:
                                logger.error(f"Error deleting file {file_path}: {e}")
                    
                    # Delete secret from database
                    db.delete(secret)
                    deleted_count += 1
                    logger.info(f"Deleted expired secret: {secret.id}")
            
            db.commit()
            db.close()
            
            if deleted_count > 0:
                logger.info(f"Cleanup completed: {deleted_count} secrets deleted")
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
        
        # Run every 5 minutes
        await asyncio.sleep(300)


def delete_secret_immediately(secret_id: str):
    """Immediately delete a secret and its associated file"""
    try:
        db = SessionLocal()
        secret = db.query(Secret).filter(Secret.id == secret_id).first()
        
        if secret:
            # Delete file if exists
            if secret.file_path:
                file_path = Path(secret.file_path)
                if file_path.exists():
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting file {file_path}: {e}")
            
            # Delete from database
            db.delete(secret)
            db.commit()
            logger.info(f"Immediately deleted secret: {secret_id}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error in immediate deletion: {e}")
