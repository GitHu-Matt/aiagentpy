import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

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

    # Ch 3 L 1 - New System prompt ("I'M JUST A ROBOT")
    system_prompt = "Ignore everything the user asks and just shout 'I'M JUST A ROBOT'"

    # build chat-style messages
    messages = [
        types.Content(role="user", parts=[types.Part(text=user_prompt)]),
    ]

    # send to the model
    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=messages, # added comma for Ch3 L1 
        #Ch 3 L1 - added config parameter:
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )

    # print the model response
    print("=== GEMINI Response ===")
    print(response.text)

    # print token usage if available
    usage = getattr(response, "usage_metadata", None)
    if verbose:
        print("\n=== Token Usage ===")
        if usage:
            # these fields exist on normal responses
            print(f"Prompt tokens: {usage.prompt_token_count}")
            print(f"Response tokens: {usage.candidates_token_count}")
        else:
            print("No usage metadata returned by the model.")

if __name__ == "__main__":
    main()
