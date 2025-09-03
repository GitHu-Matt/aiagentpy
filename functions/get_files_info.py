# functions/get_files_info.py
import os

def get_files_info(working_directory, directory="."):
    """
    Return a string describing the contents of `directory` (relative to working_directory).
    If the resolved path is outside working_directory, or is not a directory,
    return an error string prefixed with "Error:".

    Output format (each entry on its own line):
    - name: file_size=NN bytes, is_dir=True|False
    """
    try:
        # Normalize working_directory absolute path
        wd_abs = os.path.abspath(working_directory)

        # Build target path by joining (treat `directory` as relative to working_directory)
        target = os.path.abspath(os.path.join(working_directory, directory))

        # Security check: ensure target is inside working_directory
        # Use commonpath to be robust against weird paths like "../"
        try:
            common = os.path.commonpath([wd_abs, target])
        except Exception:
            return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'

        if common != wd_abs:
            return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'

        # Check that target exists and is a directory
        if not os.path.exists(target) or not os.path.isdir(target):
            return f'Error: "{directory}" is not a directory'

        # List directory contents (sorted for deterministic output)
        entries = sorted(os.listdir(target))

        lines = []
        for name in entries:
            full_path = os.path.join(target, name)
            try:
                is_dir = os.path.isdir(full_path)
                # os.path.getsize works for files and directories (on many OSes directory size is small)
                size = os.path.getsize(full_path)
                lines.append(f"- {name}: file_size={size} bytes, is_dir={is_dir}")
            except Exception as e:
                # If an error occurs while inspecting an entry, return an Error string
                return f"Error: {e}"

        return "\n".join(lines)

    except Exception as e:
        # Catch-all: always return an error string (never raise)
        return f"Error: {e}"
