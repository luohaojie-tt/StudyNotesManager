"""Virus scanning service using ClamAV."""
from typing import Optional
from loguru import logger


class VirusScanService:
    """Service for scanning files for viruses using ClamAV."""

    def __init__(self):
        """Initialize virus scan service."""
        self.clamav_available = False
        self._init_clamav()

    def _init_clamav(self):
        """Initialize ClamAV connection."""
        try:
            import pyclamd
            self.cd = pyclamd.ClamdUnixSocket()
            if self.cd.ping():
                self.clamav_available = True
                logger.info("ClamAV virus scanning service initialized")
            else:
                logger.warning("ClamAV daemon not available, virus scanning disabled")
        except ImportError:
            logger.warning("pyclamd not installed, virus scanning disabled")
            self.cd = None
        except Exception as e:
            logger.warning(f"Failed to initialize ClamAV: {e}")
            self.cd = None

    async def scan_file(self, file_content: bytes, filename: str = "uploaded_file") -> dict:
        """Scan file content for viruses.

        Args:
            file_content: File content as bytes
            filename: Filename for logging

        Returns:
            Dictionary with scan results:
                - clean: bool - True if no threats found
                - found_infected: bool - True if threats found
                - viruses: list - List of virus names found
                - status: str - Scan status
        """
        if not self.clamav_available:
            logger.info(f"Virus scanning not available, skipping scan for {filename}")
            return {
                "clean": True,
                "found_infected": False,
                "viruses": [],
                "status": "skipped"
            }

        try:
            # Scan file in memory
            scan_result = self.cd.scan_stream(file_content)

            if scan_result is None:
                # No threats found
                logger.info(f"File {filename} scanned clean")
                return {
                    "clean": True,
                    "found_infected": False,
                    "viruses": [],
                    "status": "clean"
                }
            else:
                # Threats found
                virus_names = list(scan_result.values())
                logger.error(f"File {filename} is infected: {virus_names}")
                return {
                    "clean": False,
                    "found_infected": True,
                    "viruses": virus_names,
                    "status": "infected"
                }

        except Exception as e:
            logger.error(f"Virus scan failed for {filename}: {e}")
            # Fail open: if scan fails, allow the file but log the error
            # In production, you might want to fail closed instead
            return {
                "clean": True,
                "found_infected": False,
                "viruses": [],
                "status": f"error: {str(e)}"
            }


# Global virus scan service instance
virus_scan_service = VirusScanService()
