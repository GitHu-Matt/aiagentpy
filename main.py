import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.get_files_info import schema_get_files_info  # Ch3 L2 added the import


def parse_args():
    """
    Returns: (prompt_string, verbose_bool)
    Accepts usage like:
      uv run main.py "Why is Python great?" --verbose
    or
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

    # Ch3 L2 - System prompt
    system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""

    # build chat-style messages
    messages = [
        types.Content(role="user", parts=[types.Part(text=user_prompt)]),
    ]

    # Ch3 L2 - Build Tool and config
    available_functions = types.Tool(
        function_declarations=[schema_get_files_info]
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

    # Ch3 L2 - Check if the model returned a function call plan:
    function_calls = getattr(response, "function_calls", None)
    if function_calls:
        for fc in function_calls:
            name = getattr(fc, "name", "<no-name>")
            args = getattr(fc, "args", "<no-args>")
            print(f"Calling function: {name}({args})")
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

