# functions/write_file.py
import os
#Ch3.3 block added
from google.genai import types

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Writes or overwrites a file within the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file to write to, relative to the working directory."
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The text content to write into the file."
            ),
        },
        required=["file_path", "content"],
    ),
)


def _resolve_paths(working_directory: str, user_path: str):
    """Return (base_abs, target_abs) as absolute paths."""
    base = os.path.abspath(working_directory)
    target = os.path.abspath(os.path.join(base, user_path))
    return base, target

def write_file(working_directory, file_path, content):
    """
    Safely write/overwrite a file inside `working_directory`.

    Returns a string:
      - Success:  'Successfully wrote to "<file_path>" (<n> characters written)'
      - Error:    'Error: <reason>'
    """
    try:
        base, target = _resolve_paths(working_directory, file_path)

        # Guardrail: only allow writes INSIDE the working directory
        if not (target == base or target.startswith(base + os.sep)):
            return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'

        # Ensure parent directory exists
        parent = os.path.dirname(target) or base
        if not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

        # Write/overwrite file
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)

        return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'

    except Exception as e:
        return f"Error: {e}"
