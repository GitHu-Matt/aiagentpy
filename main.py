import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import all schemas
from functions.get_files_info import schema_get_files_info
from functions.get_file_content import schema_get_file_content
from functions.write_file import schema_write_file
from functions.run_python import schema_run_python_file


def parse_args():
    """
    Returns: (prompt_string, verbose_bool)
    Accepts usage like:
      uv run main.py "Why is Python great?" --verbose
      uv run main.py Why is Python great? --verbose
    """
    raw = sys.argv[1:]  # everything after script name
    verbose = False

    # detect flags and remove them from args
    if '--verbose' in raw:
        verbose = True
        raw = [a for a in raw if a != '--verbose']
    if '-v' in raw:
        verbose = True
        raw = [a for a in raw if a != '-v']

    # if nothing left, error
    if not raw:
        print("Error: No prompt provided.\nUsage: uv run main.py \"<your prompt>\" [--verbose]")
        sys.exit(1)

    # join remaining pieces into a single prompt string (handles unquoted multi-word)
    prompt = " ".join(raw)
    return prompt, verbose


def main():
    # parse arguments
    user_prompt, verbose = parse_args()

    # optional verbose print of the user's prompt
    if verbose:
        print(f"User prompt: {user_prompt}\n")

    # load API key
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment (.env).")
        sys.exit(1)

    # create client
    client = genai.Client(api_key=api_key)

    # Ch3.3 - Expanded system prompt
    system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. 
You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory. 
You do not need to specify the working directory in your function calls 
as it is automatically injected for security reasons.
"""

    # build chat-style messages
    messages = [
        types.Content(role="user", parts=[types.Part(text=user_prompt)]),
    ]

    # make all functions available
    available_functions = types.Tool(
        function_declarations=[
            schema_get_files_info,
            schema_get_file_content,
            schema_write_file,
            schema_run_python_file,
        ]
    )

    config = types.GenerateContentConfig(
        tools=[available_functions],
        system_instruction=system_prompt,
    )

    # send to the model
    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=messages,
        config=config,
    )

    # Check if the model returned a function call plan
    function_calls = getattr(response, "function_calls", None)
    if function_calls:
        for fc in function_calls:
            name = getattr(fc, "name", "<no-name>")
            args = getattr(fc, "args", "<no-args>")
            print(f"Calling function: {name}({args})")
    else:
        print("=== GEMINI Response ===")
        print(response.text)

    # Print token usage if available
    usage = getattr(response, "usage_metadata", None)
    if verbose:
        print("\n=== Token Usage ===")
        if usage:
            print(f"Prompt tokens: {usage.prompt_token_count}")
            print(f"Response tokens: {usage.candidates_token_count}")
        else:
            print("No usage metadata returned by the model.")


if __name__ == "__main__":
    main()
