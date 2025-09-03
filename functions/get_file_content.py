# import os
from .config import MAX_CHARS
# Ch3.2 block added
from google.genai import types
import os

# Schema for get_file_content
schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Reads the contents of a file within the working directory, truncated if too long.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file to read, relative to the working directory."
            ),
        },
        required=["file_path"],
    ),
)


def get_file_content(working_directory, file_path):
    """
    Safely read a file located inside working_directory.

    Arguments:
        working_directory: path (string) that serves as the "root" sandbox
        file_path: file path relative to working_directory

    Returns:
        file contents (string) or an error string that starts with "Error:".
        If file is larger than MAX_CHARS, the returned string is truncated
        to MAX_CHARS and ends with:
            [...]File "{file_path}" truncated at {MAX_CHARS} characters
    """
    try:
        # Resolve canonical absolute paths (resolve symlinks)
        wd_real = os.path.realpath(working_directory)
        target = os.path.realpath(os.path.join(working_directory, file_path))

        # Security check: ensure target is inside the working directory
        try:
            common = os.path.commonpath([wd_real, target])
        except Exception:
            return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'

        if common != wd_real:
            return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'

        # Ensure target is a regular file
        if not os.path.isfile(target):
            return f'Error: File not found or is not a regular file: "{file_path}"'

        # Read up to MAX_CHARS + 1 so we can detect truncation
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(MAX_CHARS + 1)

        if len(content) > MAX_CHARS:
            # Truncate and append the required message
            truncated = content[:MAX_CHARS] + f'\n[...File "{file_path}" truncated at {MAX_CHARS} characters]'
            return truncated

        return content

    except Exception as e:
        return f"Error: {e}"
