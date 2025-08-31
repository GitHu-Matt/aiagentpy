import os
import sys
from dotenv import load_dotenv
from google import genai

def main():
    # Check if a prompt is provided via command line
    if len(sys.argv) < 2:
        print("Error: No prompt provided.")
        sys.exit(1)  # Exit with a non-zero status
    
    # Get the prompt from command line argument
    prompt = sys.argv[1]

    # Load environment variables from .env
    load_dotenv() 
    api_key = os.environ.get("GEMINI_API_KEY")

    # Create Gemini client
    client = genai.Client(api_key=api_key)

    # Generate content
    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=prompt
    )

    # Print response
    print("=== GEMINI Response ===")
    print(response.text)  # The text output from the model

    # Print token usage
    usage = response.usage_metadata
    print("\n=== Token Usage ===")
    print(f"Prompt tokens: {usage.prompt_token_count}")
    print(f"Response tokens: {usage.candidates_token_count}")

if __name__ == "__main__":
    main()