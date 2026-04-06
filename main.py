import os
import asyncio
from google import genai
from google.genai import types
from google.genai.errors import APIError

# =====================================================================
# GLOBAL VARIABLES & CONFIGURATION
# =====================================================================
NUM_AGENTS = 10
NUM_ROUNDS = 5
TOPIC = "Should a global, mandatory carbon tax be implemented?"

# Initialize the Gemini Client
# The client automatically picks up the GEMINI_API_KEY environment variable.
try:
    client = genai.Client()
except Exception as e:
    print(f"Warning: Could not initialize global Gemini Client. {e}")
    client = None


async def get_gemini_response(system_instruction: str, user_prompt: str, model: str = "gemini-2.5-flash") -> str:
    """
    Asynchronous wrapper for the Gemini API.
    Accepts a system instruction (persona) and a user prompt.
    Includes basic error handling for API limits or connection issues.
    """
    if not client:
        return "Error: Gemini client is not initialized. Please set the GEMINI_API_KEY environment variable."
        
    try:
        # Use the asynchronous client to generate content
        # google-genai SDK provides client.aio for async operations
        response = await client.aio.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            )
        )
        return response.text
    except APIError as e:
        # Handle specific API errors (e.g., rate limits, invalid keys)
        print(f"Gemini API Error: {e.message} (Code: {e.code})")
        return f"Error: API limit reached or invalid request. Details: {e.message}"
    except Exception as e:
        # Fallback for general exceptions
        print(f"An unexpected error occurred during the API call: {e}")
        return f"Error: {str(e)}"


async def test_ping():
    """
    Simple test script to ensure we can ping Gemini successfully.
    """
    print("Testing Gemini API wrapper...")
    print("-----------------------------")
    
    syst_inst = "You are a helpful test assistant. Respond briefly."
    prompt = "Say 'Hello, World!' and confirm you are ready."
    
    print(f"System Instruction: {syst_inst}")
    print(f"User Prompt: {prompt}")
    print("Awaiting response...\n")
    
    response = await get_gemini_response(syst_inst, prompt)
    
    print(f"Response:\n{response}")
    print("-----------------------------")


if __name__ == "__main__":
    # Ensure GEMINI_API_KEY is set in your environment
    if not os.environ.get("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY environment variable not found.")
        print("Please set it using: export GEMINI_API_KEY='your_api_key'")
        
    # Run the test
    asyncio.run(test_ping())
