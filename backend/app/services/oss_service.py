"""
Alibaba Cloud OSS Service for MinerU Integration
Handles file uploads and generates presigned URLs for document extraction
"""

import oss2
import uuid
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)


class OSService:
    """
    Alibaba Cloud OSS Service
    
    Provides:
    - File upload to OSS bucket
    - Generate presigned URLs for temporary access
    - Automatic cleanup support
    """
    
    def __init__(self):
        """Initialize OSS client with configuration from settings"""
        self.access_key_id = getattr(settings, 'oss_access_key_id', None)
        self.access_key_secret = getattr(settings, 'oss_access_key_secret', None)
        self.bucket_name = getattr(settings, 'oss_bucket', None)
        self.endpoint = getattr(settings, 'oss_endpoint', None)
        
        # Initialize OSS client if all credentials are available
        self.bucket = None
        if all([self.access_key_id, self.access_key_secret, self.bucket_name, self.endpoint]):
            try:
                auth = oss2.Auth(self.access_key_id, self.access_key_secret)
                self.bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
                logger.info(f"✅ OSS client initialized: {self.bucket_name} @ {self.endpoint}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OSS client: {e}")
                self.bucket = None
        else:
            logger.warning("⚠️ OSS credentials not fully configured")
    
    def is_configured(self) -> bool:
        """Check if OSS is properly configured"""
        return self.bucket is not None
    
    async def upload_file(
        self, 
        file_path: str, 
        object_name: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[str]:
        """
        Upload file to OSS bucket
        
        Args:
            file_path: Local file path
            object_name: Optional custom object name in OSS
            metadata: Optional metadata dict
            
        Returns:
            Object name in OSS or None if upload fails
        """
        if not self.is_configured():
            logger.error("❌ OSS not configured")
            return None
        
        try:
            # Generate object name if not provided
            if not object_name:
                file_ext = Path(file_path).suffix
                object_name = f"medicare/temp/{uuid.uuid4()}{file_ext}"
            
            logger.info(f"🔄 Uploading to OSS: {file_path} -> {object_name}")
            
            # Upload file
            self.bucket.put_object_from_file(object_name, file_path)
            
            # Set metadata if provided
            if metadata:
                self.bucket.update_object_meta(object_name, metadata)
            
            logger.info(f"✅ File uploaded to OSS: {object_name}")
            return object_name
            
        except Exception as e:
            logger.error(f"❌ OSS upload failed: {e}")
            return None
    
    def generate_presigned_url(
        self, 
        object_name: str, 
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for temporary access
        
        Args:
            object_name: Object name in OSS
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL or None if generation fails
        """
        if not self.is_configured():
            logger.error("❌ OSS not configured")
            return None
        
        try:
            # Generate presigned URL with expiration
            url = self.bucket.sign_url('GET', object_name, expiration)
            logger.info(f"✅ Generated presigned URL for {object_name} (expires in {expiration}s)")
            return url
            
        except Exception as e:
            logger.error(f"❌ Failed to generate presigned URL: {e}")
            return None
    
    async def upload_and_get_url(
        self, 
        file_path: str, 
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Upload file and immediately return presigned URL
        
        Args:
            file_path: Local file path
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL or None if operation fails
        """
        # Upload file
        object_name = await self.upload_file(file_path)
        if not object_name:
            return None
        
        # Generate presigned URL
        url = self.generate_presigned_url(object_name, expiration)
        return url
    
    def delete_object(self, object_name: str) -> bool:
        """
        Delete object from OSS
        
        Args:
            object_name: Object name in OSS
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.is_configured():
            logger.error("❌ OSS not configured")
            return False
        
        try:
            self.bucket.delete_object(object_name)
            logger.info(f"✅ Deleted from OSS: {object_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete object: {e}")
            return False
    
    def object_exists(self, object_name: str) -> bool:
        """
        Check if object exists in OSS
        
        Args:
            object_name: Object name in OSS
            
        Returns:
            True if exists, False otherwise
        """
        if not self.is_configured():
            return False
        
        try:
            return self.bucket.object_exists(object_name)
        except Exception:
            return False
    
    def health_check(self) -> dict:
        """
        Check OSS service health
        
        Returns:
            Dict with health status
        """
        if not self.is_configured():
            return {
                "healthy": False,
                "error": "OSS not configured"
            }
        
        try:
            # Try to get bucket info
            self.bucket.get_bucket_info()
            return {
                "healthy": True,
                "bucket": self.bucket_name,
                "endpoint": self.endpoint
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }


# Global OSS service instance
os_service = OSService()
