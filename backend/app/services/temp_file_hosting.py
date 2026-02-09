"""
Temporary File Hosting Service for MinerU Integration
Uploads files to temporary hosting to get public URLs for MinerU API
Includes fallback to local file server if external services fail
"""

import httpx
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TemporaryFileHosting:
    """
    Service to upload files to temporary hosting and get public URLs.
    This is a workaround for MinerU API which requires public URLs.
    
    Strategy:
    1. Try external hosting services (transfer.sh, file.io, etc.)
    2. If all fail, fall back to local file server (if configured)
    3. Return None if all methods fail
    """
    
    # Common headers to avoid blocking
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    @staticmethod
    async def upload_to_transfer_sh(file_path: str) -> Optional[str]:
        """Upload file to transfer.sh"""
        try:
            file_name = Path(file_path).name
            
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                with open(file_path, 'rb') as f:
                    response = await client.put(
                        f"https://transfer.sh/{file_name}",
                        content=f.read(),
                        headers={
                            **TemporaryFileHosting.DEFAULT_HEADERS,
                            "Content-Type": "application/octet-stream",
                            "Max-Days": "1"
                        }
                    )
                
                if response.status_code == 200:
                    url = response.text.strip()
                    logger.info(f"✅ transfer.sh upload successful: {url[:50]}...")
                    return url
                else:
                    logger.warning(f"⚠️ transfer.sh failed: HTTP {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.warning(f"⚠️ transfer.sh error: {e}")
            return None
    
    @staticmethod
    async def upload_to_file_io(file_path: str) -> Optional[str]:
        """Upload file to file.io"""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                with open(file_path, 'rb') as f:
                    files = {'file': (Path(file_path).name, f, 'application/octet-stream')}
                    response = await client.post(
                        "https://file.io",
                        files=files,
                        params={"expires": "1d"},
                        headers=TemporaryFileHosting.DEFAULT_HEADERS
                    )
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        url = result.get('link')
                        if url:
                            logger.info(f"✅ file.io upload successful: {url[:50]}...")
                            return url
                    except:
                        pass
                
                logger.warning(f"⚠️ file.io failed: HTTP {response.status_code}")
                return None
                    
        except Exception as e:
            logger.warning(f"⚠️ file.io error: {e}")
            return None
    
    @staticmethod
    async def upload_to_catbox(file_path: str) -> Optional[str]:
        """Upload file to catbox.moe (alternative service)"""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                with open(file_path, 'rb') as f:
                    data = {
                        'reqtype': 'fileupload',
                    }
                    files = {'fileToUpload': f}
                    response = await client.post(
                        "https://litterbox.catbox.moe/resources/internals/api.php",
                        data=data,
                        files=files,
                        headers=TemporaryFileHosting.DEFAULT_HEADERS
                    )
                
                if response.status_code == 200:
                    url = response.text.strip()
                    if url.startswith('http'):
                        logger.info(f"✅ catbox upload successful: {url[:50]}...")
                        return url
                
                logger.warning(f"⚠️ catbox failed: HTTP {response.status_code}")
                return None
                    
        except Exception as e:
            logger.warning(f"⚠️ catbox error: {e}")
            return None
    
    @classmethod
    async def get_public_url(cls, file_path: str, local_base_url: Optional[str] = None) -> Optional[str]:
        """
        Try multiple hosting services to get a public URL.
        
        Args:
            file_path: Path to local file
            local_base_url: Optional local file server URL (e.g., "http://files.medicare.ai/temp/")
            
        Returns:
            Public URL or None if all methods fail
        """
        services = [
            ("transfer.sh", cls.upload_to_transfer_sh),
            ("file.io", cls.upload_to_file_io),
            ("catbox.moe", cls.upload_to_catbox),
        ]
        
        # Try external services first
        for service_name, upload_func in services:
            logger.info(f"🔄 Trying {service_name}...")
            try:
                url = await upload_func(file_path)
                if url:
                    logger.info(f"✅ Successfully uploaded to {service_name}")
                    return url
            except Exception as e:
                logger.warning(f"⚠️ {service_name} error: {e}")
        
        # If external services fail, try local file server
        if local_base_url:
            logger.info(f"🔄 Falling back to local file server: {local_base_url}")
            try:
                file_name = Path(file_path).name
                local_url = f"{local_base_url.rstrip('/')}/{file_name}"
                logger.info(f"✅ Using local file URL: {local_url}")
                return local_url
            except Exception as e:
                logger.error(f"❌ Local file server fallback failed: {e}")
        
        logger.error("❌ All file hosting methods failed")
        return None
    
    @staticmethod
    def get_local_file_url(file_path: str, base_url: str) -> str:
        """
        Generate a URL for local file serving.
        
        Args:
            file_path: Local file path
            base_url: Base URL for file serving (e.g., "http://10.86.7.137:8000/files/")
            
        Returns:
            Full URL to access the file
        """
        file_name = Path(file_path).name
        return f"{base_url.rstrip('/')}/{file_name}"
