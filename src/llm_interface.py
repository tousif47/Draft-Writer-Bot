# src/llm_interface.py

# Import necessary libraries
import requests  # Used for making HTTP requests to the Ollama API
import json      # Used for handling JSON data (encoding payload, decoding response)
import os        # Used here to potentially allow overriding defaults via environment variables (optional)

# --- Configuration Constants ---
# Define default values that can be easily changed or potentially overridden
# The specific Ollama model we intend to use. ':0.5b' specifies the small version.
# os.getenv allows setting an environment variable like DWB_MODEL to use a different model.
DEFAULT_MODEL = os.getenv("DWB_MODEL", "qwen2.5:0.5b")

# The network address where the Ollama server is expected to be running.
# By default, Ollama runs on the local machine (localhost) on port 11434.
DEFAULT_OLLAMA_URL = os.getenv("DWB_OLLAMA_URL", "http://localhost:11434")

# Maximum time (in seconds) to wait for a response from the Ollama server.
REQUEST_TIMEOUT = 60

# --- Core Function ---

def generate_draft(original_message: str, instruction: str,
                   model: str = DEFAULT_MODEL,
                   ollama_url: str = DEFAULT_OLLAMA_URL) -> tuple[str | None, str | None]:
    """
    Sends the original message and user instruction to the specified local Ollama model
    using the /api/chat endpoint and returns the generated draft reply.

    Handles potential errors during the API call (connection, timeout, HTTP errors, bad responses).

    Args:
        original_message (str): The message the user received.
        instruction (str): The user's instruction on how to reply (e.g., "Say yes").
        model (str): The name of the Ollama model to query (defaults to DEFAULT_MODEL).
        ollama_url (str): The base URL of the running Ollama instance (defaults to DEFAULT_OLLAMA_URL).

    Returns:
        tuple[str | None, str | None]: A tuple containing:
            - The generated draft text (str) if the API call was successful and response valid.
            - An error message (str) describing the issue if any error occurred.
            If successful, the error message is None. If unsuccessful, the draft text is None.
    """
    # Construct the full URL for the Ollama chat API endpoint
    # rstrip('/') ensures we don't get double slashes if ollama_url already ends with one
    full_url = f"{ollama_url.rstrip('/')}/api/chat"

    # --- Prompt Engineering ---
    # Craft a clear prompt for the language model.
    # For small models like 0.5B, providing clear context and instructions
    # directly in the prompt is crucial for getting good results.
    # Using markers like "Original Message:", "My Instruction:", "Drafted Reply:" helps structure the task.
    prompt = f"""The user received the following message from someone else:
\"""
{original_message}
\"""

The user wants to send a reply based on this instruction: "{instruction}"

Draft a message that the user can send as their reply.
The reply should directly convey the user's intent based on the instruction.
IMPORTANT: Write only the reply text itself, do not act as an assistant writing about the reply. Or add anything else other the reply itself.

Reply Draft:"""

    # --- Prepare API Request ---
    # Structure the data according to the Ollama /api/chat endpoint requirements.
    # It expects a list of 'messages', similar to OpenAI's chat format.
    messages = [
        # The 'user' role contains the main prompt and context.
        {"role": "user", "content": prompt}
        # For some models or more complex chats, you might add a 'system' role message here
        # to set the overall behavior, but for this simple task, it's often sufficient
        # to include instructions in the 'user' prompt.
    ]

    # The JSON payload to send in the POST request body.
    payload = {
        "model": model,       # Specify which Ollama model to use
        "messages": messages, # The conversation history/prompt
        "stream": False       # Set to False to receive the entire response at once, not chunk by chunk
        # Optional parameters like 'temperature', 'top_p' could be added here
        # to control the creativity/randomness of the output, but we'll use defaults.
    }

    # --- Execute API Call with Error Handling ---
    try:
        # Print a debug message to console (useful during development)
        print(f"Sending request to {full_url} with model {model}...")

        # Make the HTTP POST request to the Ollama API.
        # - `json=payload`: Automatically encodes the payload dictionary as JSON
        #                   and sets the 'Content-Type' header to 'application/json'.
        # - `timeout=REQUEST_TIMEOUT`: Sets a maximum time to wait for the server response.
        response = requests.post(full_url, json=payload, timeout=REQUEST_TIMEOUT)

        # Check if the HTTP request itself was successful (status code 2xx).
        # If not (e.g., 404 Not Found, 500 Internal Server Error), this raises an HTTPError.
        response.raise_for_status()

        # If the request was successful (status code 200), parse the JSON response body.
        response_data = response.json()
        print(f"Received response: {response_data}") # Debug print

        # --- Process Successful Response ---
        # Check if the response JSON contains the expected structure.
        # The /api/chat endpoint should return a dictionary with a 'message' key,
        # which itself is a dictionary containing a 'content' key with the AI's reply.
        if 'message' in response_data and 'content' in response_data['message']:
            # Extract the generated text content.
            draft = response_data['message']['content']
            # Remove any leading/trailing whitespace from the generated text.
            return draft.strip(), None # Return (draft, None) indicating success
        else:
            # The response was received, but it's not in the format we expected.
            error_msg = f"Unexpected response format from Ollama: Missing 'message' or 'content' key."
            print(f"Error: {error_msg} Response: {response_data}")
            return None, error_msg # Return (None, error_msg)

    # --- Handle Specific Errors ---
    except requests.exceptions.ConnectionError:
        # This error occurs if the script couldn't connect to the ollama_url at all
        # (e.g., Ollama service isn't running, wrong URL/port, network issue).
        error_msg = f"Connection Error: Could not connect to Ollama at {full_url}. Is Ollama running?"
        print(error_msg)
        return None, error_msg # Return (None, error_msg)

    except requests.exceptions.Timeout:
        # This error occurs if Ollama took longer than REQUEST_TIMEOUT seconds to respond.
        error_msg = f"Timeout Error: Request to Ollama timed out after {REQUEST_TIMEOUT} seconds."
        print(error_msg)
        return None, error_msg # Return (None, error_msg)

    except requests.exceptions.HTTPError as http_err:
        # This catches errors raised by response.raise_for_status() (e.g., 4xx, 5xx responses).
        error_msg = f"HTTP Error: {http_err}. Status Code: {response.status_code}"
        # Try to include more specific error details from Ollama's response body if possible.
        try:
             # Ollama often returns JSON with an 'error' key on failure.
             error_detail = response.json().get('error', response.text)
             error_msg += f"\nOllama Response: {error_detail}"
        except (json.JSONDecodeError, AttributeError, NameError):
             # Fallback if the response isn't JSON or doesn't have 'text'.
             error_msg += f"\nRaw Response: {getattr(response, 'text', 'N/A')}"
        print(error_msg)
        return None, error_msg # Return (None, error_msg)

    except requests.exceptions.RequestException as req_err:
        # Catch any other error raised by the requests library (less common).
        error_msg = f"Request Error: An unexpected error occurred during the request: {req_err}"
        print(error_msg)
        return None, error_msg # Return (None, error_msg)

    except json.JSONDecodeError:
        # Catch errors if Ollama returns a successful status code (200) but the body isn't valid JSON.
        raw_response_text = getattr(response, 'text', 'N/A') # Get raw text safely
        error_msg = f"JSON Decode Error: Could not decode JSON response from Ollama."
        # Include the raw response in the returned error message for better debugging.
        error_msg += f"\nRaw Response: {raw_response_text}"
        print(error_msg)
        return None, error_msg # Return (None, error_msg)

    except Exception as e:
        # A general catch-all for any other unexpected Python errors within the try block.
        error_msg = f"An unexpected error occurred in generate_draft: {type(e).__name__} - {e}"
        print(error_msg)
        return None, error_msg # Return (None, error_msg)


# --- Direct Execution Block ---
# This code only runs when you execute this file directly (e.g., `python src/llm_interface.py`).
# It's useful for quick manual testing of this specific module.
if __name__ == '__main__':
    print(f"--- Testing llm_interface.py ---")
    print(f"Attempting to connect to Ollama at {DEFAULT_OLLAMA_URL} with model {DEFAULT_MODEL}")
    print("!!! IMPORTANT: Ensure Ollama is running and the model is downloaded (`ollama pull qwen2.5:0.5b`) before running this test. !!!")

    # Example inputs for testing
    test_message = "Are you available for a quick call tomorrow morning?"
    test_instruction = "Suggest 10 AM or ask for another time."

    # Call the function
    draft, error = generate_draft(test_message, test_instruction)

    # Print the results
    print("\n--- Result ---")
    if error:
        print(f"Error occurred:\n{error}")
    elif draft:
        print(f"Generated Draft:\n---\n{draft}\n---")
    else:
        # This case might happen if the function somehow returns (None, None)
        print("Failed to generate draft (No specific error message returned, check logs).")
    print("--------------")