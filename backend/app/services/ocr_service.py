"""Baidu OCR service for text recognition."""
from typing import Optional

from aip import AipOcr
from loguru import logger

from app.core.config import settings


class BaiduOCRService:
    """Baidu OCR service for text extraction from images."""

    def __init__(self):
        """Initialize Baidu OCR service."""
        self.app_id = settings.BAIDU_OCR_APP_ID
        self.api_key = settings.BAIDU_OCR_API_KEY
        self.secret_key = settings.BAIDU_OCR_SECRET_KEY

        if self.app_id and self.api_key and self.secret_key:
            self.client = AipOcr(self.app_id, self.api_key, self.secret_key)
            logger.info("Baidu OCR service initialized")
        else:
            logger.warning("Baidu OCR credentials not configured, using mock mode")
            self.client = None

    async def recognize_text(self, image_content: bytes) -> tuple[Optional[str], Optional[float]]:
        """Recognize text from image.

        Args:
            image_content: Image content as bytes

        Returns:
            Tuple of (recognized_text, confidence_score)
        """
        if not self.client:
            # Mock mode for development
            logger.info("Mock OCR recognition")
            return "This is mock OCR text for development testing.", 0.95

        try:
            # Call Baidu OCR API
            result = self.client.basicGeneral(image_content)

            if "error_code" in result:
                logger.error(f"Baidu OCR error: {result['error_msg']}")
                return None, None

            # Extract text from result
            if "words_result" in result and result["words_result"]:
                recognized_lines = [item["words"] for item in result["words_result"]]
                recognized_text = "\n".join(recognized_lines)

                # Calculate average confidence
                confidences = [
                    item.get("probability", {}).get("average", 0.9)
                    for item in result["words_result"]
                ]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

                logger.info(f"OCR recognition successful, {len(recognized_lines)} lines extracted")
                return recognized_text, avg_confidence

            return None, None

        except Exception as e:
            logger.error(f"Failed to recognize text: {e}")
            return None, None

    async def recognize_text_accurate(self, image_content: bytes) -> tuple[Optional[str], Optional[float]]:
        """Recognize text from image with higher accuracy.

        Args:
            image_content: Image content as bytes

        Returns:
            Tuple of (recognized_text, confidence_score)
        """
        if not self.client:
            # Mock mode for development
            logger.info("Mock accurate OCR recognition")
            return "This is mock accurate OCR text for development testing.", 0.98

        try:
            # Call Baidu OCR API with higher accuracy
            result = self.client.basicAccurate(image_content)

            if "error_code" in result:
                logger.error(f"Baidu OCR error: {result['error_msg']}")
                return None, None

            # Extract text from result
            if "words_result" in result and result["words_result"]:
                recognized_lines = [item["words"] for item in result["words_result"]]
                recognized_text = "\n".join(recognized_lines)

                # Calculate average confidence
                confidences = [
                    item.get("probability", {}).get("average", 0.95)
                    for item in result["words_result"]
                ]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

                logger.info(f"Accurate OCR recognition successful, {len(recognized_lines)} lines extracted")
                return recognized_text, avg_confidence

            return None, None

        except Exception as e:
            logger.error(f"Failed to recognize text accurately: {e}")
            return None, None


# Global OCR service instance
ocr_service = BaiduOCRService()
