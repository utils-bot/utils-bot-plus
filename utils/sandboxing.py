"""
Secure Python code execution sandboxing utilities
"""

import asyncio
import tempfile
import shutil
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import structlog

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    docker = None
    DOCKER_AVAILABLE = False

logger = structlog.get_logger("sandboxing")

# Import image manager
try:
    from .image_manager import image_manager
    IMAGE_MANAGER_AVAILABLE = True
except ImportError:
    image_manager = None
    IMAGE_MANAGER_AVAILABLE = False

@dataclass
class SandboxConfig:
    """Configuration for sandbox execution"""
    timeout: int = 10  # seconds
    memory_limit: str = "128m"  # Docker memory limit
    cpu_limit: float = 0.5  # CPU limit (fraction of one CPU)
    max_output_size: int = 8192  # Max output characters
    max_file_size: int = 1024 * 1024  # 1MB max file size
    allowed_packages: List[str] = field(default_factory=lambda: [
        "math", "random", "itertools", "collections", "functools",
        "operator", "string", "re", "datetime", "json", "base64",
        "hashlib", "urllib", "statistics", "decimal", "fractions"
    ])
    blocked_modules: List[str] = field(default_factory=lambda: [
        "os", "sys", "subprocess", "socket", "urllib.request",
        "urllib.parse", "urllib.error", "http", "ftplib", "smtplib",
        "imaplib", "poplib", "telnetlib", "socketserver", "threading",
        "multiprocessing", "concurrent", "asyncio", "importlib",
        "__import__", "eval", "exec", "compile", "open", "file",
        "input", "raw_input"
    ])

@dataclass
class ExecutionResult:
    """Result of code execution"""
    success: bool
    output: str
    error: str = ""
    execution_time: float = 0.0
    memory_used: str = ""
    exit_code: int = 0
    files_created: List[str] = field(default_factory=list)

class SecureSandbox:
    """Secure Python code execution sandbox using Docker"""
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.client = None
        self._initialize_docker()
    
    def _initialize_docker(self):
        """Initialize Docker client with error handling"""
        if not DOCKER_AVAILABLE:
            logger.warning("Docker not available - sandbox will be disabled")
            self.client = None
            return
            
        try:
            self.client = docker.from_env()  # type: ignore
            # Test Docker connection
            self.client.ping()
            logger.info("Docker client initialized successfully")
            
            # Verify we can pull/build images
            try:
                # Try to pull a minimal Python image for testing
                self.client.images.pull("python:3.11-alpine")
                logger.info("Docker image pull test successful")
            except Exception as e:
                logger.warning("Docker image pull failed, will build locally", error=str(e))
                
        except Exception as e:
            logger.error("Failed to initialize Docker client", error=str(e))
            self.client = None
    
    async def execute_code(
        self,
        code: str,
        files: Optional[Dict[str, bytes]] = None,
        stdin_data: str = ""
    ) -> ExecutionResult:
        """
        Execute Python code in a secure sandbox
        
        Args:
            code: Python code to execute
            files: Optional files to include in execution (filename -> content)
            stdin_data: Optional stdin input for the program
            
        Returns:
            ExecutionResult with execution details
        """
        if not self.client:
            return ExecutionResult(
                success=False,
                output="",
                error="Docker not available - falling back to subprocess sandbox"
            )
        
        # Quick check if images are available
        try:
            from .image_manager import image_manager
            if not getattr(image_manager, 'built_images', None):
                return ExecutionResult(
                    success=False,
                    output="",
                    error="Docker images not ready - falling back to subprocess sandbox"
                )
        except Exception:
            # If image manager check fails, continue with execution attempt
            pass
        
        start_time = datetime.now()
        temp_dir = None
        
        try:
            # Create temporary directory for execution
            temp_dir = tempfile.mkdtemp(prefix="sandbox_")
            sandbox_path = Path(temp_dir)
            
            # Prepare execution environment
            await self._prepare_sandbox_environment(sandbox_path, code, files, stdin_data)
            
            # Execute code in Docker container
            result = await self._run_in_container(sandbox_path)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            # Check for created files
            result.files_created = await self._get_created_files(sandbox_path)
            
            return result
            
        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Container execution timed out (container startup/shutdown took too long). Code timeout limit: {self.config.timeout}s",
                execution_time=self.config.timeout
            )
        except Exception as e:
            logger.error("Sandbox execution failed", error=str(e))
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution failed: {str(e)}"
            )
        finally:
            # Cleanup
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning("Failed to cleanup temp directory", error=str(e))
    
    async def _prepare_sandbox_environment(
        self,
        sandbox_path: Path,
        code: str,
        files: Optional[Dict[str, bytes]],
        stdin_data: str
    ):
        """Prepare the sandbox environment with code and files"""
        
        # Create main Python file with security wrapper
        main_code = self._wrap_code_with_security(code)
        (sandbox_path / "main.py").write_text(main_code, encoding="utf-8")
        
        # Create stdin file if provided
        if stdin_data:
            (sandbox_path / "input.txt").write_text(stdin_data, encoding="utf-8")
        
        # Add user files if provided
        if files:
            for filename, content in files.items():
                if self._is_safe_filename(filename):
                    file_path = sandbox_path / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Check file size
                    if len(content) > self.config.max_file_size:
                        raise ValueError(f"File {filename} too large (max {self.config.max_file_size} bytes)")
                    
                    file_path.write_bytes(content)
    
    def _wrap_code_with_security(self, code: str) -> str:
        """Wrap user code with security restrictions"""
        wrapper = f'''
import sys
import signal
import traceback
import time
import io
from contextlib import redirect_stdout, redirect_stderr

# Security: Block dangerous imports
BLOCKED_MODULES = {self.config.blocked_modules}

class ImportBlock:
    def __init__(self, blocked_modules):
        self.blocked_modules = set(blocked_modules)
        self.original_import = __builtins__.__import__
    
    def __call__(self, name, *args, **kwargs):
        if name in self.blocked_modules:
            raise ImportError(f"Module '{{name}}' is blocked for security reasons")
        
        # Block relative imports that might escape sandbox
        if name.startswith('.'):
            raise ImportError("Relative imports are not allowed")
            
        return self.original_import(name, *args, **kwargs)

# Install import blocker
__builtins__.__import__ = ImportBlock(BLOCKED_MODULES)

# Timeout handler
def timeout_handler(signum, frame):
    raise TimeoutError(f"Code execution timed out after {self.config.timeout} seconds")

# Set up timeout - this limits ONLY the user code execution
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm({self.config.timeout})

# Capture output
stdout_capture = io.StringIO()
stderr_capture = io.StringIO()

try:
    start_time = time.time()
    
    # Redirect stdin if input file exists
    try:
        with open('input.txt', 'r') as f:
            sys.stdin = f
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # User code starts here
{self._indent_code(code, 16)}
                # User code ends here
    except FileNotFoundError:
        # No input file, use normal stdin
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # User code starts here
{self._indent_code(code, 12)}
            # User code ends here
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Get outputs
    stdout_content = stdout_capture.getvalue()
    stderr_content = stderr_capture.getvalue()
    
    # Limit output size
    max_size = {self.config.max_output_size}
    if len(stdout_content) > max_size:
        stdout_content = stdout_content[:max_size] + "\\n... (output truncated)"
    
    print("__SANDBOX_STDOUT__")
    print(stdout_content)
    print("__SANDBOX_STDERR__")
    print(stderr_content)
    print(f"__SANDBOX_TIME__{{execution_time}}")
    print("__SANDBOX_SUCCESS__")
    
except Exception as e:
    error_msg = traceback.format_exc()
    print("__SANDBOX_STDOUT__")
    print("")
    print("__SANDBOX_STDERR__")
    print(error_msg)
    if "timed out" in str(e).lower():
        print("__SANDBOX_TIMEOUT__")
    print("__SANDBOX_ERROR__")
finally:
    signal.alarm(0)  # Cancel timeout
'''
        return wrapper
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by specified number of spaces"""
        indent = " " * spaces
        return "\n".join(indent + line for line in code.split("\n"))
    
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe (no path traversal, etc.)"""
        # Normalize path and check for path traversal
        normalized = os.path.normpath(filename)
        if normalized.startswith("..") or os.path.isabs(normalized):
            return False
        
        # Check for dangerous characters
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*"]
        if any(char in filename for char in dangerous_chars):
            return False
        
        return True
    
    async def _run_in_container(self, sandbox_path: Path) -> ExecutionResult:
        """Run code in Docker container using pre-built images with resource limits"""
        if not self.client:
            return ExecutionResult(
                success=False,
                output="",
                error="Docker client not available"
            )

        try:
            # Determine which image to use based on code requirements
            image_type = self._select_appropriate_image(sandbox_path)
            
            # Get pre-built image from image manager
            image_tag = None
            if IMAGE_MANAGER_AVAILABLE and image_manager:
                image_tag = await image_manager.get_image_for_language(image_type)
                if not image_tag:
                    # Fallback to basic image if enhanced not available
                    if image_type == "python-enhanced":
                        logger.warning("Enhanced image not ready, falling back to basic")
                        image_tag = await image_manager.get_image_for_language("python")
            
            if not image_tag:
                return ExecutionResult(
                    success=False,
                    output="",
                    error="No sandbox images available. Image manager not ready or Docker images not built yet."
                )
            
            # Type guard - we know client is not None here
            client = self.client
            
            # Mount the sandbox directory as volume
            volumes = {str(sandbox_path): {'bind': '/app', 'mode': 'ro'}}
            
            # Run container with resource limits
            container = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.containers.run(
                    image_tag,
                    command=["python", "-u", "/app/main.py"],
                    detach=True,
                    mem_limit=self.config.memory_limit,
                    cpu_period=100000,
                    cpu_quota=int(100000 * self.config.cpu_limit),
                    network_disabled=True,
                    read_only=True,
                    tmpfs={"/tmp": "size=100m,noexec"},
                    volumes=volumes,
                    working_dir="/app",
                    user="sandbox"
                )
            )
            
            try:
                # Wait for container with longer timeout to account for startup
                # The actual Python code timeout is handled by signal.alarm() inside the container
                container_timeout = self.config.timeout + 5  # Extra time for container startup/shutdown
                
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: container.wait(timeout=container_timeout)
                    ),
                    timeout=container_timeout + 2
                )
                
                # Get logs
                logs = container.logs(stdout=True, stderr=True).decode('utf-8')
                
                # Parse output
                return self._parse_container_output(logs, result['StatusCode'])
                
            finally:
                # Cleanup container
                try:
                    container.remove(force=True)
                except Exception:
                    pass
                    
        except asyncio.TimeoutError:
            raise
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Container execution failed: {str(e)}"
            )
    
    def _select_appropriate_image(self, sandbox_path: Path) -> str:
        """Select appropriate Docker image based on code requirements"""
        try:
            # Read the main.py file to check for enhanced library usage
            main_py = (sandbox_path / "main.py").read_text()
            
            # Check if code uses advanced libraries
            enhanced_indicators = [
                "numpy", "np.", "scipy", "pandas", "pd.", "matplotlib", 
                "plt.", "seaborn", "sklearn", "sympy", "requests"
            ]
            
            if any(indicator in main_py for indicator in enhanced_indicators):
                return "python-enhanced"
            
            return "python"
            
        except Exception:
            # Default to basic image if analysis fails
            return "python"
    
    def _parse_container_output(self, logs: str, exit_code: int) -> ExecutionResult:
        """Parse container output to extract results"""
        try:
            lines = logs.split("\n")
            
            stdout = ""
            stderr = ""
            execution_time = 0.0
            success = False
            is_timeout = False
            
            current_section = None
            
            for line in lines:
                if line == "__SANDBOX_STDOUT__":
                    current_section = "stdout"
                elif line == "__SANDBOX_STDERR__":
                    current_section = "stderr"
                elif line.startswith("__SANDBOX_TIME__"):
                    execution_time = float(line.replace("__SANDBOX_TIME__", ""))
                elif line == "__SANDBOX_SUCCESS__":
                    success = True
                elif line == "__SANDBOX_ERROR__":
                    success = False
                elif line == "__SANDBOX_TIMEOUT__":
                    is_timeout = True
                    success = False
                elif current_section == "stdout":
                    stdout += line + "\n"
                elif current_section == "stderr":
                    stderr += line + "\n"
            
            # Handle timeout case specifically
            if is_timeout:
                return ExecutionResult(
                    success=False,
                    output=stdout.rstrip(),
                    error=f"Code execution timed out after {self.config.timeout} seconds",
                    execution_time=self.config.timeout,
                    exit_code=exit_code
                )
            
            return ExecutionResult(
                success=success and exit_code == 0,
                output=stdout.rstrip(),
                error=stderr.rstrip() if stderr.strip() else "",
                execution_time=execution_time,
                exit_code=exit_code
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=logs[:1000] if logs else "",
                error=f"Failed to parse output: {str(e)}"
            )
    
    async def _get_created_files(self, sandbox_path: Path) -> List[str]:
        """Get list of files created during execution"""
        try:
            created_files = []
            for item in sandbox_path.iterdir():
                if item.name not in ["main.py", "Dockerfile", "requirements.txt", "input.txt"]:
                    if item.is_file() and item.stat().st_size <= self.config.max_file_size:
                        created_files.append(item.name)
            return created_files
        except Exception:
            return []

# Global sandbox instance
sandbox = SecureSandbox()

# Fallback function that automatically chooses the best available sandbox
async def execute_code_safely(code: str, files=None, stdin_data="", config=None):
    """
    Execute code using the best available sandbox with intelligent fallback
    
    Priority:
    1. Docker sandbox with pre-built images (fastest, most secure)
    2. Fallback subprocess sandbox (slower but reliable)
    """
    from .fallback_sandbox import FallbackSandbox
    
    # Use provided config or default
    sandbox_config = config or SandboxConfig()
    
    # Try Docker sandbox first if available
    if sandbox.client:
        try:
            # Check if image manager has images ready
            from .image_manager import image_manager
            
            # Quick check if any images are available
            if image_manager.built_images:
                logger.info("Using Docker sandbox with pre-built images")
                return await sandbox.execute_code(code, files, stdin_data)
            else:
                logger.info("Docker available but images not ready, using fallback")
                
        except Exception as e:
            logger.warning(f"Docker sandbox failed, using fallback: {e}")
    
    # Use fallback sandbox
    logger.info("Using fallback subprocess sandbox")
    fallback = FallbackSandbox(sandbox_config)
    return await fallback.execute_code(code, files, stdin_data)
