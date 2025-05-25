"""
Docker image management for sandbox optimization
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
import structlog

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    docker = None
    DOCKER_AVAILABLE = False

logger = structlog.get_logger("image_manager")

class SandboxImageManager:
    """Manages pre-built sandbox images for optimal performance"""
    
    def __init__(self):
        self.client = None
        self.built_images: Dict[str, str] = {}  # language -> image_tag
        self.building_lock = asyncio.Lock()
        self.build_status: Dict[str, bool] = {}  # language -> is_building
        self.last_cleanup = datetime.now()
        self.cleanup_interval = timedelta(hours=1)
        
    async def initialize(self) -> bool:
        """Initialize Docker client and start building base images"""
        if not DOCKER_AVAILABLE:
            logger.warning("Docker not available - image management disabled")
            return False
            
        try:
            if DOCKER_AVAILABLE:
                self.client = docker.from_env()
                self.client.ping()
                logger.info("Docker client initialized for image management")
                
                # Start building base images in background
                asyncio.create_task(self._build_base_images())
                
                return True
            else:
                logger.warning("Docker not available - image management disabled")
                return False
        except Exception as e:
            logger.error("Failed to initialize Docker for image management", error=str(e))
            return False
    
    async def _build_base_images(self):
        """Build base sandbox images for supported languages"""
        languages = ["python", "python-enhanced"]  # Can add cpp, java later
        
        for language in languages:
            try:
                await self._build_language_image(language)
            except Exception as e:
                logger.error(f"Failed to build {language} image", error=str(e))
    
    async def _build_language_image(self, language: str):
        """Build optimized image for a specific language"""
        async with self.building_lock:
            if language in self.build_status and self.build_status[language]:
                return  # Already building
                
            self.build_status[language] = True
            
            try:
                logger.info(f"Building optimized {language} sandbox image...")
                
                # Create temporary directory for build context
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Generate optimized Dockerfile
                    dockerfile_content = self._generate_optimized_dockerfile(language)
                    (temp_path / "Dockerfile").write_text(dockerfile_content)
                    
                    # Generate requirements for Python
                    if language.startswith("python"):
                        requirements = self._generate_requirements(language)
                        (temp_path / "requirements.txt").write_text(requirements)
                    
                    # Build image
                    image_tag = f"utils-bot-sandbox-{language}:latest"
                    
                    if self.client:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: self.client.images.build(
                                path=str(temp_path),
                                tag=image_tag,
                                rm=True,
                                forcerm=True,
                                quiet=False,
                                nocache=False  # Use cache for faster builds
                            )
                        )
                    
                    self.built_images[language] = image_tag
                    logger.info(f"Successfully built {language} sandbox image: {image_tag}")
                    
            except Exception as e:
                logger.error(f"Failed to build {language} image", error=str(e))
            finally:
                self.build_status[language] = False
    
    def _generate_optimized_dockerfile(self, language: str) -> str:
        """Generate optimized Dockerfile for specific language"""
        
        if language == "python":
            return """
# Optimized Python sandbox image
FROM python:3.11-alpine

# Install essential packages in one layer
RUN apk add --no-cache gcc musl-dev libffi-dev

# Create non-root user
RUN adduser -D -s /bin/sh sandbox

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN if [ -s requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Remove build dependencies to reduce size
RUN apk del gcc musl-dev libffi-dev

# Security: Remove dangerous tools
RUN rm -rf /usr/bin/wget /usr/bin/curl || true

# Switch to non-root user
USER sandbox

# Default command (will be overridden)
CMD ["python", "-u", "-c", "print('Sandbox Ready')"]
"""
        
        elif language == "python-enhanced":
            return """
# Enhanced Python sandbox with scientific libraries
FROM python:3.11-alpine

# Install comprehensive build dependencies
RUN apk add --no-cache \\
    gcc g++ musl-dev \\
    libffi-dev \\
    gfortran \\
    openblas-dev \\
    lapack-dev \\
    freetype-dev \\
    libpng-dev

# Create non-root user
RUN adduser -D -s /bin/sh sandbox

# Set working directory
WORKDIR /app

# Upgrade pip for better package resolution
RUN pip install --no-cache-dir --upgrade pip

# Copy and install requirements
COPY requirements.txt .
RUN if [ -s requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Keep essential runtime libraries, remove only build tools
RUN apk del gcc g++ musl-dev libffi-dev gfortran

# Security: Remove dangerous tools
RUN rm -rf /usr/bin/wget /usr/bin/curl || true

# Switch to non-root user
USER sandbox

# Default command
CMD ["python", "-u", "-c", "print('Enhanced Sandbox Ready')"]
"""
        
        else:
            # Default to basic Python
            return self._generate_optimized_dockerfile("python")
    
    def _generate_requirements(self, language: str) -> str:
        """Generate requirements.txt for language"""
        
        if language == "python":
            return """
# Basic Python packages (compatible versions)
numpy
sympy
"""
        
        elif language == "python-enhanced":
            return """
# Enhanced Python packages for competitive programming (compatible versions)
numpy
scipy
sympy
networkx
# Skip matplotlib and pandas for now to avoid build issues
"""
        
        return ""
    
    async def get_image_for_language(self, language: str = "python") -> Optional[str]:
        """Get pre-built image for language, build if necessary"""
        # Normalize language
        if language in ["py", "python", "python3"]:
            language = "python"
        elif language in ["python-enhanced", "competitive"]:
            language = "python-enhanced"
        else:
            language = "python"  # Default fallback
        
        # Return cached image if available
        if language in self.built_images:
            return self.built_images[language]
        
        # Check if currently building
        if language in self.build_status and self.build_status[language]:
            # Wait for build to complete (with timeout)
            for _ in range(30):  # Wait up to 30 seconds
                await asyncio.sleep(1)
                if language in self.built_images:
                    return self.built_images[language]
            
            logger.warning(f"Timeout waiting for {language} image build")
            return None
        
        # Start building if not available
        logger.info(f"Image for {language} not ready, building...")
        await self._build_language_image(language)
        
        return self.built_images.get(language)
    
    async def cleanup_old_images(self, force: bool = False):
        """Clean up old sandbox images"""
        if not force and datetime.now() - self.last_cleanup < self.cleanup_interval:
            return
        
        if not self.client:
            return
            
        try:
            # Get all sandbox images
            images = self.client.images.list(filters={"label": "utils-bot-sandbox"})
            
            # Remove old/unused images (keep current ones)
            current_tags = set(self.built_images.values())
            removed_count = 0
            
            for image in images:
                if not any(tag in current_tags for tag in image.tags):
                    try:
                        self.client.images.remove(image.id, force=True)
                        removed_count += 1
                    except Exception as e:
                        logger.debug(f"Failed to remove image {image.id}", error=str(e))
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old sandbox images")
            
            self.last_cleanup = datetime.now()
            
        except Exception as e:
            logger.error("Failed to cleanup old images", error=str(e))
    
    def get_image_info(self) -> Dict[str, dict]:
        """Get information about built images"""
        info = {}
        
        for language, tag in self.built_images.items():
            try:
                if self.client:
                    image = self.client.images.get(tag)
                    info[language] = {
                        "tag": tag,
                        "size_mb": round(image.attrs["Size"] / 1024 / 1024, 1),
                        "created": image.attrs["Created"],
                        "ready": True
                    }
            except Exception:
                info[language] = {
                    "tag": tag,
                    "size_mb": "unknown",
                    "created": "unknown",
                    "ready": False
                }
        
        # Add building status
        for language, building in self.build_status.items():
            if building and language not in info:
                info[language] = {
                    "tag": f"utils-bot-sandbox-{language}:latest",
                    "building": True,
                    "ready": False
                }
        
        return info
    
    async def rebuild_all_images(self):
        """Force rebuild all images"""
        logger.info("Rebuilding all sandbox images...")
        
        # Clear cache
        self.built_images.clear()
        
        # Rebuild
        await self._build_base_images()
        
        logger.info("Finished rebuilding all images")

# Global instance
image_manager = SandboxImageManager()
