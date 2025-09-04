import os
import sys
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

# Import schemas AND real functions
from functions.get_files_info import get_files_info, schema_get_files_info
from functions.get_file_content import get_file_content, schema_get_file_content
from functions.write_file import write_file, schema_write_file
from functions.run_python import run_python_file, schema_run_python_file


def parse_args():
    """
    Returns: (prompt_string, verbose_bool)
    Usage:
      uv run main.py "Your prompt here" [--verbose|-v]
      uv run main.py Your prompt here --verbose
    """
    raw = sys.argv[1:]
    verbose = False

    if '--verbose' in raw:
        verbose = True
        raw = [a for a in raw if a != '--verbose']
    if '-v' in raw:
        verbose = True
        raw = [a for a in raw if a != '-v']

    if not raw:
        print('Error: No prompt provided.\nUsage: uv run main.py "<your prompt>" [--verbose]')
        sys.exit(1)

    prompt = " ".join(raw)
    return prompt, verbose


# --- Helpers added in Ch 4.1 fixes ---

def _normalize_relative_path(p: str) -> str:
    """
    Make a path safe & relative:
    - strip leading slashes
    - strip leading 'calculator/' (since we inject working_directory='calculator')
    """
    if not isinstance(p, str):
        return p
    while p.startswith("/"):
        p = p[1:]
    if p.startswith("calculator/"):
        p = p[len("calculator/"):]
    return p


def call_model_with_retries(client, model, messages, config, *, retries=3, base_delay=1.0, verbose=False):
    """
    Call client.models.generate_content with simple exponential backoff
    for transient errors like 503/UNAVAILABLE or 429/rate limit.
    """
    attempt = 0
    while True:
        try:
            return client.models.generate_content(
                model=model,
                contents=messages,
                config=config,
            )
        except genai_errors.ServerError as e:
            # 5xx errors like 503
            attempt += 1
            if attempt > retries:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            if verbose:
                print(f"(retry {attempt}/{retries}) transient server error {getattr(e, 'status_code', '?')}, waiting {delay:.1f}s…")
            time.sleep(delay)
        except genai_errors.APIError as e:
            status = getattr(e, "status", "")
            code = getattr(e, "status_code", "")
            if status in ("RESOURCE_EXHAUSTED", "UNAVAILABLE") or code in (429, 503):
                attempt += 1
                if attempt > retries:
                    raise
                delay = base_delay * (2 ** (attempt - 1))
                if verbose:
                    print(f"(retry {attempt}/{retries}) API error {status or code}, waiting {delay:.1f}s…")
                time.sleep(delay)
            else:
                raise


def call_function(function_call_part, verbose=False):
    """
    Execute one of our declared functions based on LLM's request.

    Returns a types.Content with a tool function_response part:
      { "result": "<string result or error>" }
    """
    name = function_call_part.name
    args = dict(function_call_part.args or {})

    # Normalize common path args so "pkg/render.py" and "calculator/pkg/render.py" both work
    if "file_path" in args and isinstance(args["file_path"], str):
        args["file_path"] = _normalize_relative_path(args["file_path"])
    if "directory" in args and isinstance(args["directory"], str):
        args["directory"] = _normalize_relative_path(args["directory"])

    if verbose:
        print(f"Calling function: {name}({args})")
    else:
        print(f" - Calling function: {name}")

    # Security: the LLM can't control the working directory
    args["working_directory"] = "calculator"

    function_map = {
        "get_files_info": get_files_info,
        "get_file_content": get_file_content,
        "write_file": write_file,
        "run_python_file": run_python_file,
    }

    func = function_map.get(name)
    if not func:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=name,
                    response={"error": f"Unknown function: {name}"}
                )
            ],
        )

    try:
        result = func(**args)
    except Exception as e:
        result = f"Error while executing {name}: {e}"

    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=name,
                response={"result": result},
            )
        ],
    )


def main():
    # 0) args & key
    user_prompt, verbose = parse_args()
    if verbose:
        print(f"User prompt: {user_prompt}\n")

    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment (.env).")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # 1) system prompt (tools + loop behavior)
    system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, you may plan and call tools repeatedly until the task is complete.
You can perform the following operations:
- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

Rules:
- Use short, focused tool calls.
- Use paths RELATIVE to the working directory only (do NOT prefix with "calculator/").
- The working directory is injected automatically.
- When you are finished, stop calling tools and provide a concise final answer to the user.
"""

    # 2) initial conversation messages
    messages = [
        types.Content(role="user", parts=[types.Part(text=user_prompt)]),
    ]

    # 3) register all tools
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

    # 4) agent loop
    MAX_STEPS = 20
    for step in range(1, MAX_STEPS + 1):
        if verbose:
            print(f"\n--- Iteration {step} ---")

        # Ask the model "what's next?" with full conversation (with retries)
        response = call_model_with_retries(
            client,
            "gemini-2.0-flash-001",
            messages,
            config,
            retries=3,
            base_delay=1.0,
            verbose=verbose,
        )

        # Always append the model's content (includes any function-call plan)
        candidates = getattr(response, "candidates", []) or []
        for cand in candidates:
            if cand.content:
                messages.append(cand.content)

        # Did the model ask to call any tools?
        function_calls = getattr(response, "function_calls", None)
        if function_calls:
            for fc in function_calls:
                tool_reply = call_function(fc, verbose=verbose)

                # Sanity check + add tool response to conversation
                parts = getattr(tool_reply, "parts", [])
                if not parts or not hasattr(parts[0], "function_response"):
                    raise RuntimeError("Fatal: function call did not return a function_response")

                messages.append(tool_reply)

                if verbose:
                    resp_dict = parts[0].function_response.response
                    print(f"-> {resp_dict}")

            # Next iteration: the model will see tool outputs and continue
            continue

        # If no tool calls, check for final text
        if getattr(response, "text", None):
            print("Final response:")
            print(response.text)
            break
    else:
        print("Stopped: reached maximum number of steps without a final response.")

    # Optional token usage
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
