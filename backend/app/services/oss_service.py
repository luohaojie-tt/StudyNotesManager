"""Aliyun OSS service for file storage."""
import io
from typing import Optional

import oss2
from loguru import logger

from app.core.config import settings


class OSSService:
    """Aliyun OSS service for file upload and management."""

    def __init__(self):
        """Initialize OSS service."""
        self.access_key_id = settings.ALIYUN_OSS_ACCESS_KEY_ID
        self.access_key_secret = settings.ALIYUN_OSS_ACCESS_KEY_SECRET
        self.bucket_name = settings.ALIYUN_OSS_BUCKET_NAME
        self.endpoint = settings.ALIYUN_OSS_ENDPOINT

        # Initialize auth and bucket
        if self.access_key_id and self.access_key_secret:
            self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
            logger.info("OSS service initialized")
        else:
            logger.warning("OSS credentials not configured, using mock mode")
            self.bucket = None

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> str:
        """Upload file to OSS.

        Args:
            file_content: File content as bytes
            filename: Original filename
            content_type: MIME type of the file

        Returns:
            URL of the uploaded file

        Raises:
            Exception: If upload fails
        """
        if not self.bucket:
            # Mock mode for development
            logger.info(f"Mock upload: {filename}")
            return f"https://mock-oss-url/{filename}"

        try:
            # Generate unique filename
            import uuid
            from datetime import datetime

            ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
            unique_filename = (
                f"notes/{datetime.utcnow().strftime('%Y%m%d')}/"
                f"{uuid.uuid4()}.{ext}"
            )

            # Upload to OSS
            result = self.bucket.put_object(
                unique_filename,
                file_content,
                headers={"Content-Type": content_type} if content_type else {},
            )

            if result.status == 200:
                file_url = f"https://{self.bucket_name}.{self.endpoint}/{unique_filename}"
                logger.info(f"File uploaded successfully: {file_url}")
                return file_url
            else:
                raise Exception(f"Upload failed with status {result.status}")

        except Exception as e:
            logger.error(f"Failed to upload file to OSS: {e}")
            raise

    async def delete_file(self, file_url: str) -> bool:
        """Delete file from OSS.

        Args:
            file_url: URL of the file to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.bucket:
            logger.info(f"Mock delete: {file_url}")
            return True

        try:
            # Extract filename from URL
            filename = file_url.split(f"/{self.bucket_name}.{self.endpoint}/")[-1]

            # Delete from OSS
            result = self.bucket.delete_object(filename)

            if result.status == 204:
                logger.info(f"File deleted successfully: {filename}")
                return True
            else:
                logger.error(f"Failed to delete file: {result.status}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete file from OSS: {e}")
            return False

    async def generate_thumbnail(
        self, file_content: bytes, content_type: str
    ) -> Optional[bytes]:
        """Generate thumbnail for image files.

        Args:
            file_content: Original image content
            content_type: MIME type of the image

        Returns:
            Thumbnail image content or None
        """
        try:
            # Only process images
            if not content_type.startswith("image/"):
                return None

            # For PDFs and other formats, we'd need additional libraries
            # For now, return the original content as a simple implementation
            # In production, use PIL or similar for thumbnail generation

            # Simple implementation: return original for images
            # TODO: Implement actual thumbnail generation with PIL
            return file_content[:10000]  # Simple truncate for demo

        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return None


# Global OSS service instance
oss_service = OSSService()
