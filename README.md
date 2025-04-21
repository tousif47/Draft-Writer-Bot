# Draft Writer Bot

A simple, privacy-focused Windows desktop application that uses a locally running small language model (via Ollama) to help you quickly draft replies to messages, with streaming output.

**(Add a Screenshot Here)**

## Features

* **Simple Interface:** Easily paste the original message and your instruction.
* **AI-Powered Drafts:** Generates draft replies based on your intent using a local LLM.
* **Streaming Output:** See the AI response appear word-by-word.
* **Local & Private:** Uses Ollama to run a language model directly on your machine. Your messages and instructions are **never** sent to any external cloud service.
* **Offline Capable:** Works without an internet connection (after initial setup of Ollama and the model).
* **Lightweight:** Designed to work with very small LLMs (like Qwen 2.5 0.5B) suitable for less powerful computers.
* **Copy to Clipboard:** Easily copy the fully generated draft.
* **Clear Inputs:** Button to quickly clear all text fields.
* **Status Bar:** Provides feedback on the current application state.
* **Dark Theme:** Uses a modern dark theme for the UI.

## Prerequisites

Before you install and run Draft Writer Bot, you need:

1.  **Python:** Version 3.9 or higher recommended (Developed with 3.13). You can download Python from [python.org](https://www.python.org/).
2.  **Ollama:** You **must** install Ollama. Follow the instructions for Windows on [ollama.com](https://ollama.com/).
3.  **Ollama Model:** After installing Ollama, you need to download a language model for it to use. The recommended lightweight model is `qwen2.5:0.5b`. Open your Command Prompt or PowerShell and run:
    ```bash
    ollama pull qwen2.5:0.5b
    ```
    Wait for the download to complete. You can choose other models, but ensure your computer meets their resource requirements (check the Ollama library). Make sure the Ollama application/service is running before starting Draft Writer Bot.

## Installation

*(Instructions below assume it will be publish to PyPI. Update as needed.)*

**Option 1: From PyPI (Recommended once published)**

```bash
Add the pip command here

**Option 2: From Source (Using Git)**

More TBA