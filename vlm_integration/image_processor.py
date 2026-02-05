"""
Image Processor for Dashboard Snapshots
=======================================

This module handles all image processing tasks for the VLM integration:
- Loading and validating snapshot images
- Resizing and normalizing for optimal VLM processing
- Finding the latest snapshot
- Image quality checks

Part of the Visual-Time-Series Reasoning Pipeline (Step 2: Image Processing)
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime

try:
    from PIL import Image  # type: ignore
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from django.conf import settings  # type: ignore
except Exception:
    # Fallback when Django is not installed or settings are not available.
    # Use MEDIA_ROOT env var if set, otherwise default to ./media
    import os
    from types import SimpleNamespace
    settings = SimpleNamespace(MEDIA_ROOT=os.environ.get('MEDIA_ROOT', str(Path.cwd() / "media")))

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Handles image processing for dashboard snapshots.

    Responsibilities:
    - Locate and validate snapshot images
    - Resize images for optimal VLM processing
    - Provide metadata about snapshots
    """

    # Optimal dimensions for LLaVA processing
    # LLaVA works well with images around 512-1024px
    TARGET_MAX_DIMENSION = 1024
    TARGET_MIN_DIMENSION = 256

    # Supported image formats
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.webp'}

    def __init__(self, media_root: Optional[str] = None):
        """
        Initialize the image processor.

        Args:
            media_root: Base directory for media files (default: Django MEDIA_ROOT)
        """
        self.media_root = Path(media_root or settings.MEDIA_ROOT)
        self.snapshots_dir = self.media_root / "snapshots"

    def ensure_snapshots_dir(self) -> bool:
        """Ensure the snapshots directory exists."""
        try:
            self.snapshots_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create snapshots directory: {e}")
            return False

    def get_snapshot_path(self, filename: str) -> Optional[Path]:
        """
        Get the full path to a snapshot file.

        Args:
            filename: The snapshot filename

        Returns:
            Path object or None if not found
        """
        path = self.snapshots_dir / filename
        if path.exists() and path.is_file():
            return path
        return None

    def list_snapshots(self) -> List[Tuple[Path, datetime]]:
        """
        List all snapshot files with their modification times.

        Returns:
            List of (path, mtime) tuples, sorted by mtime descending
        """
        snapshots = []

        if not self.snapshots_dir.exists():
            return snapshots

        for file_path in self.snapshots_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                snapshots.append((file_path, mtime))

        # Sort by modification time, newest first
        snapshots.sort(key=lambda x: x[1], reverse=True)
        return snapshots

    def get_latest_snapshot(self) -> Optional[Path]:
        """
        Get the path to the most recent snapshot.

        Returns:
            Path to the latest snapshot or None if no snapshots exist
        """
        snapshots = self.list_snapshots()
        if snapshots:
            return snapshots[0][0]
        return None

    def validate_image(self, image_path: Path) -> Tuple[bool, str]:
        """
        Validate that an image file is suitable for VLM processing.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (is_valid, message)
        """
        if not image_path.exists():
            return False, f"Image not found: {image_path}"

        if not image_path.is_file():
            return False, f"Not a file: {image_path}"

        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported format: {image_path.suffix}"

        # Check file size (too small might be corrupted, too large might be slow)
        file_size = image_path.stat().st_size
        if file_size < 1000:  # Less than 1KB
            return False, "Image file too small, might be corrupted"
        if file_size > 50_000_000:  # More than 50MB
            return False, "Image file too large for processing"

        # If PIL is available, check image integrity
        if PIL_AVAILABLE:
            try:
                with Image.open(image_path) as img:
                    img.verify()
                # Reopen after verify (verify leaves file in bad state)
                with Image.open(image_path) as img:
                    width, height = img.size
                    if width < 100 or height < 100:
                        return False, "Image dimensions too small"
            except Exception as e:
                return False, f"Invalid image file: {e}"

        return True, "Image is valid"

    def get_image_info(self, image_path: Path) -> Optional[dict]:
        """
        Get metadata about an image.

        Args:
            image_path: Path to the image

        Returns:
            Dict with image metadata or None if failed
        """
        if not PIL_AVAILABLE:
            return {
                "path": str(image_path),
                "filename": image_path.name,
                "size_bytes": image_path.stat().st_size if image_path.exists() else 0,
            }

        try:
            with Image.open(image_path) as img:
                return {
                    "path": str(image_path),
                    "filename": image_path.name,
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": image_path.stat().st_size,
                }
        except Exception as e:
            logger.error(f"Failed to get image info: {e}")
            return None

    def prepare_for_vlm(
        self,
        image_path: Path,
        max_dimension: Optional[int] = None
    ) -> Tuple[Optional[Path], str]:
        """
        Prepare an image for VLM processing (resize if needed).

        For LLaVA, images work best at moderate resolutions (512-1024px).
        This method resizes large images while maintaining aspect ratio.

        Args:
            image_path: Path to the original image
            max_dimension: Maximum width or height (default: TARGET_MAX_DIMENSION)

        Returns:
            Tuple of (processed_image_path, status_message)
            If no processing needed, returns the original path.
        """
        max_dim = max_dimension or self.TARGET_MAX_DIMENSION

        # Validate first
        valid, message = self.validate_image(image_path)
        if not valid:
            return None, message

        if not PIL_AVAILABLE:
            # If PIL not available, just return original
            return image_path, "PIL not available, using original image"

        try:
            with Image.open(image_path) as img:
                width, height = img.size

                # Check if resizing is needed
                if width <= max_dim and height <= max_dim:
                    return image_path, "Image already optimal size"

                # Calculate new dimensions maintaining aspect ratio
                if width > height:
                    new_width = max_dim
                    new_height = int(height * (max_dim / width))
                else:
                    new_height = max_dim
                    new_width = int(width * (max_dim / height))

                # Resize with high quality
                resized = img.resize(
                    (new_width, new_height),
                    Image.Resampling.LANCZOS
                )

                # Save to a temporary processed file
                processed_name = f"processed_{image_path.name}"
                processed_path = self.snapshots_dir / processed_name

                # Convert RGBA to RGB if needed for JPEG
                if resized.mode == 'RGBA' and processed_path.suffix.lower() in ['.jpg', '.jpeg']:
                    resized = resized.convert('RGB')

                resized.save(processed_path, quality=95, optimize=True)

                return processed_path, f"Resized from {width}x{height} to {new_width}x{new_height}"

        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            return None, f"Processing failed: {e}"


def get_latest_snapshot_path() -> Optional[str]:
    """
    Convenience function to get the latest snapshot path as a string.

    Returns:
        Path string to the latest snapshot or None
    """
    processor = ImageProcessor()
    path = processor.get_latest_snapshot()
    return str(path) if path else None


def validate_snapshot(image_path: str) -> Tuple[bool, str]:
    """
    Convenience function to validate a snapshot image.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (is_valid, message)
    """
    processor = ImageProcessor()
    return processor.validate_image(Path(image_path))
