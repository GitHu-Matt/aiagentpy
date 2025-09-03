import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import all schemas and the real functions
from functions.get_files_info import get_files_info, schema_get_files_info
from functions.get_file_content import get_file_content, schema_get_file_content
from functions.write_file import write_file, schema_write_file
from functions.run_python import run_python_file, schema_run_python_file


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

# Ch3.4 - added the call_function()

def call_function(function_call_part, verbose=False):
    """
    Execute one of our declared functions based on LLM's request.

    Args:
        function_call_part: a types.FunctionCall with .name and .args
        verbose: if True, print detailed info

    Returns:
        types.Content with a tool function_response part
    """
    function_name = function_call_part.name
    args = dict(function_call_part.args or {})  # copy args dict safely

    if verbose:
        print(f"Calling function: {function_name}({args})")
    else:
        print(f" - Calling function: {function_name}")

    # Always inject working_directory (LLM cannot set this)
    args["working_directory"] = "calculator"

    # Map from string name -> actual Python function
    function_map = {
        "get_files_info": get_files_info,
        "get_file_content": get_file_content,
        "write_file": write_file,
        "run_python_file": run_python_file,
    }

    if function_name not in function_map:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )

    try:
        result = function_map[function_name](**args)
    except Exception as e:
        result = f"Error while executing {function_name}: {e}"

    # Wrap result into LLM-friendly Content
    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"result": result},
            )
        ],
    )


def main():
    # parse arguments
    user_prompt, verbose = parse_args()

    # optional verbose print of the user's prompt (before sending)
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

    # system prompt
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

    # build available functions
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

    # handle model response
    function_calls = getattr(response, "function_calls", None)
    if function_calls:
        for fc in function_calls:
            function_call_result = call_function(fc, verbose=verbose)

            # Verify we actually got a function_response
            parts = getattr(function_call_result, "parts", [])
            if not parts or not hasattr(parts[0], "function_response"):
                raise RuntimeError("Fatal: function call did not return a function_response")

            response_dict = parts[0].function_response.response
            if verbose:
                print(f"-> {response_dict}")
    else:
        print("=== GEMINI Response ===")
        print(response.text)

    # print token usage if available
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
