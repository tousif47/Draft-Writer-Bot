# src/llm_interface.py

import httpx
import json
import os
import asyncio

# --- Configuration Constants ---
DEFAULT_MODEL = os.getenv("DWB_MODEL", "qwen2.5:0.5b")
DEFAULT_OLLAMA_URL = os.getenv("DWB_OLLAMA_URL", "http://localhost:11434")
REQUEST_TIMEOUT = 60.0 # Timeout for HTTP requests (as float)

# --- Core Async Function with Streaming & Callbacks ---
async def generate_draft_async(
    original_message: str,
    instruction: str,

    # --- Callback functions provided by the UI ---
    on_chunk: callable,  # Called with each piece of text received
    on_error: callable,  # Called when an error occurs
    on_done: callable,   # Called when generation finishes successfully
    
    # --- Optional configuration ---
    model: str = DEFAULT_MODEL,
    ollama_url: str = DEFAULT_OLLAMA_URL
):
    """
    Sends the message/instruction to Ollama asynchronously, streams the response,
    and uses callback functions to update the UI.

    Args:
        original_message: The message received by the user.
        instruction: The user's instruction on how to reply.
        on_chunk: Callback function accepting a string (text chunk).
        on_error: Callback function accepting a string (error message).
        on_done: Callback function accepting no arguments, called on success.
        model: The name of the Ollama model.
        ollama_url: The base URL of the Ollama API.
    """
    full_url = f"{ollama_url.rstrip('/')}/api/chat"

    # Prompt optimized for small models and clarity
    prompt = f"""Task: Draft a reply message based on user instructions.
User received message:
\"""
{original_message}
\"""
User instruction for reply: "{instruction}"

Your Response MUST be ONLY the drafted reply message itself, suitable for the user to copy and paste directly.
Do NOT include any preamble, explanation, or conversation like "Here is the draft:" or "Okay, I drafted this:".
Output ONLY the reply text.

Reply Draft:"""

    messages = [{"role": "user", "content": prompt}]

    payload = {
        "model": model,
        "messages": messages,
        "stream": True  # Enable streaming response
    }

    try:
        # Use httpx.AsyncClient for async requests
        # `timeout=REQUEST_TIMEOUT` applies to connection and read timeouts
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            # `stream=True` with httpx requires using a context manager for the request
            async with client.stream("POST", full_url, json=payload) as response:
                # Check for HTTP errors immediately after getting the response headers
                # Note: httpx raises HTTPStatusError for 4xx/5xx by default with stream=True
                # if response.is_error wasn't sufficient, but raise_for_status() works well.
                response.raise_for_status()

                # Process the stream chunk by chunk
                async for line in response.aiter_lines():
                    if line:
                        try:
                            # Each line in the stream is a JSON object
                            chunk_data = json.loads(line)

                            # Check for errors within the stream response itself
                            if chunk_data.get("error"):
                                error_msg = f"Ollama stream error: {chunk_data['error']}"
                                print(error_msg)
                                on_error(error_msg)
                                return # Stop processing on stream error

                            # Extract the text chunk from the 'message' part
                            if chunk_data.get("done") is False and chunk_data.get("message", {}).get("content"):
                                text_chunk = chunk_data["message"]["content"]
                                on_chunk(text_chunk) # Send chunk to UI via callback

                            # Check if this chunk indicates the end of the stream
                            if chunk_data.get("done"):
                                print("Stream finished successfully.")
                                on_done() # Signal successful completion to UI
                                return # Exit the function

                        except json.JSONDecodeError:
                            error_msg = f"Error decoding JSON chunk: {line}"
                            print(error_msg)
                            on_error(error_msg)
                            return # Stop processing on decode error
                        except Exception as e_chunk:
                            # Catch other unexpected errors during chunk processing
                            error_msg = f"Error processing stream chunk: {type(e_chunk).__name__} - {e_chunk}"
                            print(error_msg)
                            on_error(error_msg)
                            return

    # --- Handle Errors During Initial Connection or Request Setup ---
    except httpx.ConnectError as e_conn:
        error_msg = f"Connection Error: Could not connect to Ollama at {full_url}. Is Ollama running?\nDetails: {e_conn}"
        print(error_msg)
        on_error(error_msg)

    except httpx.TimeoutException as e_timeout:
        error_msg = f"Timeout Error: Request to Ollama timed out after {REQUEST_TIMEOUT} seconds.\nDetails: {e_timeout}"
        print(error_msg)
        on_error(error_msg)

    except httpx.HTTPStatusError as e_http:
        # Error raised by response.raise_for_status() for 4xx/5xx status codes
        error_body = "N/A"

        try:
            # Try to read the response body for more details
            error_body = await e_http.response.aread()
            error_body = error_body.decode()

            # Try parsing as JSON, fallback to raw text
            try:
                error_detail = json.loads(error_body).get('error', error_body)
            except json.JSONDecodeError:
                error_detail = error_body
        
        except Exception as e_read:
            error_detail = f"(Could not read error response body: {e_read})"

        error_msg = f"HTTP Error: {e_http.response.status_code} {e_http.response.reason_phrase} for URL {e_http.request.url}.\nOllama Response: {error_detail}"
        print(error_msg)
        on_error(error_msg)

    except httpx.RequestError as e_req:
        # Other request-related errors (e.g., invalid URL)
        error_msg = f"Request Error: An unexpected error occurred during the request setup.\nDetails: {e_req}"
        print(error_msg)
        on_error(error_msg)

    except Exception as e_general:
        # Catch any other unexpected errors
        error_msg = f"An unexpected error occurred in generate_draft_async: {type(e_general).__name__} - {e_general}"
        print(error_msg)
        on_error(error_msg)


# --- Direct Execution Block (for basic async testing) ---
async def main_test():
    """Helper async function to test generate_draft_async directly."""
    
    print(f"--- Testing llm_interface.py (async) ---")
    print(f"Attempting to connect to Ollama at {DEFAULT_OLLAMA_URL} with model {DEFAULT_MODEL}")
    print("!!! IMPORTANT: Ensure Ollama is running and the model is downloaded (`ollama pull qwen2.5:0.5b`) before running this test. !!!")

    test_message = "Can we reschedule our meeting from 2 PM to 3 PM?"
    test_instruction = "Agree to 3 PM."

    # Define simple print callbacks for testing
    def print_chunk(chunk):
        print(f"Received chunk: '{chunk}'")

    def print_error(err):
        print(f"\n--- Error Callback --- \n{err}\n--------------------")

    def print_done():
        print("\n--- Done Callback ---")

    # Run the async function
    await generate_draft_async(
        test_message,
        test_instruction,
        on_chunk=print_chunk,
        on_error=print_error,
        on_done=print_done
    )
    print("-------------------------------------")


if __name__ == '__main__':
    # Run the async test function using asyncio
    try:
        asyncio.run(main_test())
    except KeyboardInterrupt:
        print("Test interrupted.")