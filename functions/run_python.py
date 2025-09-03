# functions/run_python.py
import os
import sys
import subprocess

def run_python_file(working_directory, file_path, args=None):
    """
    Execute a Python file inside working_directory with optional args.

    Returns:
      - On success: a string containing STDOUT and STDERR blocks, and exit code if non-zero.
      - On failure or guardrail violation: an Error:... string.
    """
    if args is None:
        args = []

    try:
        # Resolve real (canonical) absolute paths to handle symlinks safely
        wd_real = os.path.realpath(working_directory)
        target = os.path.realpath(os.path.join(working_directory, file_path))

        # Guardrail: ensure target is inside the working directory
        try:
            common = os.path.commonpath([wd_real, target])
        except Exception:
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

        if common != wd_real:
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

        # Check file exists
        if not os.path.exists(target):
            return f'Error: File "{file_path}" not found.'

        # Check extension is .py
        if not target.endswith(".py"):
            return f'Error: "{file_path}" is not a Python file.'

        # Build command using the same Python interpreter that's running this code (keeps venv)
        cmd = [sys.executable, target] + list(args)

        # Execute with timeout, capture output, set cwd to working directory
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=wd_real,
            timeout=30
        )

        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()

        parts = []
        if stdout:
            parts.append("STDOUT:\n" + stdout)
        if stderr:
            parts.append("STDERR:\n" + stderr)
        if completed.returncode != 0:
            parts.append(f"Process exited with code {completed.returncode}")

        if not parts:
            return "No output produced."

        # Join sections with blank line between them for readability
        return "\n\n".join(parts)

    except subprocess.TimeoutExpired as e:
        return f'Error: executing Python file: Timeout after {e.timeout} seconds'
    except Exception as e:
        return f'Error: executing Python file: {e}'
