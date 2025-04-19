# tests/test_llm_interface.py

# Import necessary libraries
import pytest                # The testing framework we'll use
import requests              # We need to reference requests exceptions
import json                  # Need this for JSONDecodeError simulation
# Import the function we want to test from our source code
import src
from src.llm_interface import generate_draft, DEFAULT_OLLAMA_URL, DEFAULT_MODEL

# --- Test Fixtures (Optional Setup) ---
# Define standard inputs for tests to avoid repetition
TEST_MSG = "Can you review this document?"
TEST_INSTR = "Ask when they need it by."
EXPECTED_URL = f"{DEFAULT_OLLAMA_URL}/api/chat"

# --- Test Cases ---
# Each function starting with 'test_' is automatically discovered by pytest as a test case.
# The 'mocker' argument is provided by the pytest-mock plugin to help us mock objects.

def test_generate_draft_success(mocker):
    """
    Tests the scenario where Ollama returns a successful response
    with the expected JSON structure.
    """
    # Arrange: Define the expected inputs and outputs for this test
    expected_draft = "Sure, I can review it. When do you need it by?"
    # Simulate the JSON data Ollama would return on success
    mock_ollama_response_json = {
        "model": DEFAULT_MODEL,
        "created_at": "2025-04-19T19:49:00.000Z", # Example timestamp
        "message": {
            "role": "assistant",
            "content": f" {expected_draft} " # Simulate potential leading/trailing spaces
        },
        "done": True,
        "total_duration": 1500000000, # Example duration
        "load_duration": 500000,
        "prompt_eval_count": 20,
        "prompt_eval_duration": 100000000,
        "eval_count": 30,
        "eval_duration": 400000000
    }

    # Mock the 'requests.post' function using pytest-mock's 'mocker' fixture.
    # - We tell mocker to replace 'requests.post' *within the scope* of 'src.llm_interface'.
    # - We configure the mock object that replaces it:
    mock_post_response = mocker.Mock()              # Create a mock object to be returned by requests.post
    mock_post_response.status_code = 200             # Simulate HTTP 200 OK status
    mock_post_response.json.return_value = mock_ollama_response_json # Tell the mock's json() method what to return
    mock_post_response.raise_for_status.return_value = None # Simulate no HTTP error being raised
    # Apply the patch to the function within the module we are testing
    mocker.patch('src.llm_interface.requests.post', return_value=mock_post_response)

    # Act: Call the function we are testing with the test inputs
    actual_draft, actual_error = generate_draft(TEST_MSG, TEST_INSTR)

    # Assert: Verify that the results are what we expected
    assert actual_draft == expected_draft # Check if the draft matches and whitespace was stripped
    assert actual_error is None           # Check that no error message was returned
    # Verify that requests.post was actually called once
    src.llm_interface.requests.post.assert_called_once()
    # Optional: Verify the arguments passed to requests.post
    call_args, call_kwargs = src.llm_interface.requests.post.call_args
    assert call_args[0] == EXPECTED_URL # Check the URL
    assert call_kwargs['json']['model'] == DEFAULT_MODEL # Check the model in the payload
    # Check that the prompt was constructed correctly within the payload
    assert TEST_MSG in call_kwargs['json']['messages'][0]['content']
    assert TEST_INSTR in call_kwargs['json']['messages'][0]['content']
    assert call_kwargs['json']['stream'] is False # Check stream is False
    assert 'timeout' in call_kwargs # Check that timeout was likely passed

def test_generate_draft_connection_error(mocker):
    """
    Tests that the function correctly handles a ConnectionError
    (e.g., Ollama server is not running).
    """
    # Arrange: Configure the mock 'requests.post' to raise ConnectionError when called
    mocker.patch('src.llm_interface.requests.post', side_effect=requests.exceptions.ConnectionError)

    # Act: Call the function
    draft, error = generate_draft("Any message", "Any instruction")

    # Assert: Verify the function returned None for the draft and an error message
    assert draft is None
    assert error is not None
    assert "Connection Error" in error # Check if the error message is appropriate
    assert DEFAULT_OLLAMA_URL in error # Check if the URL is mentioned in the error

def test_generate_draft_timeout_error(mocker):
    """
    Tests that the function correctly handles a Timeout error.
    """
    # Arrange: Configure the mock 'requests.post' to raise Timeout when called
    mocker.patch('src.llm_interface.requests.post', side_effect=requests.exceptions.Timeout)

    # Act: Call the function
    draft, error = generate_draft("Any message", "Any instruction")

    # Assert: Verify the function returned None for the draft and an error message
    assert draft is None
    assert error is not None
    assert "Timeout Error" in error # Check if the error message is appropriate

def test_generate_draft_http_error(mocker):
    """
    Tests handling of an HTTPError (e.g., Ollama returns 503 Service Unavailable).
    """
    # Arrange: Configure the mock response object
    mock_post_response = mocker.Mock()
    mock_post_response.status_code = 503 # Simulate Service Unavailable
    mock_post_response.text = '{"error": "Model qwen2.5:0.5b is currently loading"}' # Example error body
    # Make raise_for_status actually raise an HTTPError when called
    mock_post_response.raise_for_status.side_effect = requests.exceptions.HTTPError("503 Server Error")
    # Make json() return the error detail when called (for error message construction)
    mock_post_response.json.return_value = {"error": "Model qwen2.5:0.5b is currently loading"}
    mocker.patch('src.llm_interface.requests.post', return_value=mock_post_response)

    # Act: Call the function
    draft, error = generate_draft("Any message", "Any instruction")

    # Assert: Verify the function returned None for the draft and an error message
    assert draft is None
    assert error is not None
    assert "HTTP Error" in error # Check for general HTTP error text
    assert "503" in error        # Check if status code is mentioned
    assert "Model qwen2.5:0.5b is currently loading" in error # Check if Ollama detail is included

def test_generate_draft_unexpected_json_format(mocker):
    """
    Tests handling of a successful HTTP response (200) but with unexpected JSON content
    (e.g., missing the 'message' key).
    """
    # Arrange: Mock response with status 200 but incomplete JSON
    mock_post_response = mocker.Mock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = {"model": DEFAULT_MODEL, "done": True} # Missing 'message'
    mock_post_response.raise_for_status.return_value = None # Don't raise HTTPError
    mocker.patch('src.llm_interface.requests.post', return_value=mock_post_response)

    # Act: Call the function
    draft, error = generate_draft("Any message", "Any instruction")

    # Assert: Verify the function returned None for the draft and an error message
    assert draft is None
    assert error is not None
    assert "Unexpected response format" in error # Check for the specific error message

def test_generate_draft_non_json_response(mocker):
    """
    Tests handling of a successful HTTP response (200) but the body is not valid JSON.
    """
    # Arrange: Mock response with status 200 but invalid JSON body
    mock_post_response = mocker.Mock()
    mock_post_response.status_code = 200
    mock_post_response.text = "<html><body>Gateway Timeout</body></html>" # Simulate HTML error page
    # Make the mock's json() method raise a JSONDecodeError
    mock_post_response.json.side_effect = json.JSONDecodeError("Expecting value", doc="", pos=0)
    mock_post_response.raise_for_status.return_value = None # Don't raise HTTPError
    mocker.patch('src.llm_interface.requests.post', return_value=mock_post_response)

    # Act: Call the function
    draft, error = generate_draft("Any message", "Any instruction")

    # Assert: Verify the function returned None for the draft and an error message
    assert draft is None
    assert error is not None
    assert "JSON Decode Error" in error # Check for the specific error message
    assert "Gateway Timeout" in error   # Check if raw response text is included in error