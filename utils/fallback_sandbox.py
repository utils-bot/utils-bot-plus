"""
Fallback execution system for when Docker is not available
"""

import asyncio
import tempfile
import shutil
import os
import sys
import platform
from pathlib import Path
from typing import Dict, Optional
import structlog

# Only import Unix-specific modules on Unix systems
if platform.system() != "Windows":
    import subprocess
    import signal
    import resource
else:
    # Fallback for Windows
    import subprocess

from .sandboxing import ExecutionResult, SandboxConfig

logger = structlog.get_logger("fallback_sandbox")

class FallbackSandbox:
    """Fallback sandbox using subprocess with limited security"""
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
    
    async def execute_code(
        self,
        code: str,
        files: Optional[Dict[str, bytes]] = None,
        stdin_data: str = ""
    ) -> ExecutionResult:
        """
        Execute Python code using subprocess (LIMITED SECURITY)
        
        WARNING: This is a fallback with limited security.
        Use Docker sandbox for production.
        """
        temp_dir = None
        
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="fallback_sandbox_")
            sandbox_path = Path(temp_dir)
            
            # Prepare code
            main_code = self._wrap_code_for_subprocess(code)
            main_file = sandbox_path / "main.py"
            main_file.write_text(main_code, encoding="utf-8")
            
            # Add stdin file if provided
            if stdin_data:
                stdin_file = sandbox_path / "input.txt"
                stdin_file.write_text(stdin_data, encoding="utf-8")
            
            # Add user files if provided
            if files:
                for filename, content in files.items():
                    if self._is_safe_filename(filename):
                        file_path = sandbox_path / filename
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_bytes(content)
            
            # Execute with subprocess
            result = await self._run_subprocess(sandbox_path / "main.py", stdin_data)
            
            # Check for created files
            result.files_created = self._get_created_files(sandbox_path)
            
            return result
            
        except Exception as e:
            logger.error("Fallback execution failed", error=str(e))
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
    
    def _wrap_code_for_subprocess(self, code: str) -> str:
        """Wrap code with basic security measures"""
        wrapper = f'''
import sys
import signal
import traceback
import time
import io
import os
from contextlib import redirect_stdout, redirect_stderr

# Basic import restrictions (limited effectiveness)
BLOCKED_IMPORTS = {self.config.blocked_modules}

original_import = __builtins__.__import__

def restricted_import(name, *args, **kwargs):
    if name in BLOCKED_IMPORTS:
        raise ImportError(f"Import of '{{name}}' is restricted")
    return original_import(name, *args, **kwargs)

__builtins__.__import__ = restricted_import

# Set resource limits (Unix only)
try:
    import resource
    # Limit memory to 128MB
    resource.setrlimit(resource.RLIMIT_AS, (128 * 1024 * 1024, 128 * 1024 * 1024))
    # Limit CPU time
    resource.setrlimit(resource.RLIMIT_CPU, ({self.config.timeout}, {self.config.timeout}))
except:
    pass  # Windows or other systems

# Timeout handler
def timeout_handler(signum, frame):
    raise TimeoutError("Execution timed out")

try:
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm({self.config.timeout})
except:
    pass  # Windows doesn't support SIGALRM

# Capture output
stdout_capture = io.StringIO()
stderr_capture = io.StringIO()

try:
    start_time = time.time()
    
    # Redirect stdin if input file exists
    if os.path.exists('input.txt'):
        with open('input.txt', 'r') as f:
            sys.stdin = f
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # User code starts here
{self._indent_code(code, 16)}
                # User code ends here
    else:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # User code starts here
{self._indent_code(code, 12)}
            # User code ends here
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    stdout_content = stdout_capture.getvalue()
    stderr_content = stderr_capture.getvalue()
    
    # Limit output size
    max_size = {self.config.max_output_size}
    if len(stdout_content) > max_size:
        stdout_content = stdout_content[:max_size] + "\\n... (output truncated)"
    
    print("__FALLBACK_STDOUT__")
    print(stdout_content)
    print("__FALLBACK_STDERR__")
    print(stderr_content)
    print(f"__FALLBACK_TIME__{{execution_time}}")
    print("__FALLBACK_SUCCESS__")
    
except Exception as e:
    error_msg = traceback.format_exc()
    print("__FALLBACK_STDOUT__")
    print("")
    print("__FALLBACK_STDERR__")
    print(error_msg)
    print("__FALLBACK_ERROR__")
finally:
    try:
        signal.alarm(0)
    except:
        pass
'''
        return wrapper
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by specified number of spaces"""
        indent = " " * spaces
        return "\n".join(indent + line for line in code.split("\n"))
    
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe"""
        normalized = os.path.normpath(filename)
        if normalized.startswith("..") or os.path.isabs(normalized):
            return False
        
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*"]
        if any(char in filename for char in dangerous_chars):
            return False
        
        return True
    
    async def _run_subprocess(self, script_path: Path, stdin_data: str) -> ExecutionResult:
        """Run Python script using subprocess"""
        try:
            # Change to script directory
            cwd = script_path.parent
            
            # Create process
            process = await asyncio.create_subprocess_exec(
                'python', str(script_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            # Run with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=stdin_data.encode() if stdin_data else None),
                    timeout=self.config.timeout + 2
                )
                
                return self._parse_subprocess_output(
                    stdout.decode('utf-8', errors='ignore'),
                    stderr.decode('utf-8', errors='ignore'),
                    process.returncode or 0
                )
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Execution timed out after {self.config.timeout} seconds",
                    execution_time=self.config.timeout
                )
                
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Subprocess execution failed: {str(e)}"
            )
    
    def _parse_subprocess_output(self, stdout: str, stderr: str, exit_code: int) -> ExecutionResult:
        """Parse subprocess output"""
        try:
            lines = stdout.split("\n")
            
            output = ""
            error = stderr
            execution_time = 0.0
            success = False
            
            current_section = None
            
            for line in lines:
                if line == "__FALLBACK_STDOUT__":
                    current_section = "stdout"
                elif line == "__FALLBACK_STDERR__":
                    current_section = "stderr"
                elif line.startswith("__FALLBACK_TIME__"):
                    execution_time = float(line.replace("__FALLBACK_TIME__", ""))
                elif line == "__FALLBACK_SUCCESS__":
                    success = True
                elif line == "__FALLBACK_ERROR__":
                    success = False
                elif current_section == "stdout":
                    output += line + "\n"
                elif current_section == "stderr" and not error:
                    error += line + "\n"
            
            return ExecutionResult(
                success=success and exit_code == 0,
                output=output.rstrip(),
                error=error.rstrip() if error and error.strip() else "",
                execution_time=execution_time,
                exit_code=exit_code
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=stdout[:1000] if stdout else "",
                error=f"Failed to parse output: {str(e)}"
            )
    
    def _get_created_files(self, sandbox_path: Path) -> list:
        """Get list of files created during execution"""
        try:
            created_files = []
            for item in sandbox_path.iterdir():
                if item.name not in ["main.py", "input.txt"]:
                    if item.is_file() and item.stat().st_size <= self.config.max_file_size:
                        created_files.append(item.name)
            return created_files
        except Exception:
            return []

# Global fallback sandbox instance
fallback_sandbox = FallbackSandbox()
