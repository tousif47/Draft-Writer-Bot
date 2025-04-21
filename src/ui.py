# src/ui.py

import customtkinter as ctk
from tkinter import messagebox
import asyncio  # Required for running the async function
import queue    # Used for thread-safe communication
import threading # Used to run the async network call in a separate thread

# Import the async backend function
from llm_interface import generate_draft_async

# --- Set Appearance ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# --- Constants for UI Update Queue ---
UPDATE_CHUNK = "CHUNK"
UPDATE_ERROR = "ERROR"
UPDATE_DONE = "DONE"
UPDATE_STATUS = "STATUS" # Optional: For direct status updates

class DraftBotApp:
    """
    Main application window using CustomTkinter.
    Handles async LLM calls (via threading), streaming output, status updates, and clearing.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Draft Writer Bot v2 (Async/Threaded)")
        self.root.minsize(550, 600)

        self.is_generating = False
        self.ui_update_queue = queue.Queue()

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=2)
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_rowconfigure(6, weight=3)

        self._create_widgets()
        self.check_ui_queue() # Start checking the queue for UI updates

    def _create_widgets(self):
        """Creates and arranges all the necessary CustomTkinter widgets."""
        PAD_X = 15
        PAD_Y_TOP = 15
        PAD_Y_INTER = 7
        BUTTON_PAD_Y = 10

        # --- Input Sections ---
        original_label = ctk.CTkLabel(self.root, text="1. Paste Original Message:")
        original_label.grid(row=0, column=0, sticky="w", padx=PAD_X, pady=(PAD_Y_TOP, 0))
        self.original_msg_text = ctk.CTkTextbox(self.root, wrap="word", corner_radius=6)
        self.original_msg_text.grid(row=1, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y_INTER)

        instruction_label = ctk.CTkLabel(self.root, text="2. Your Instruction (e.g., 'Politely decline', 'Say yes'):")
        instruction_label.grid(row=2, column=0, sticky="w", padx=PAD_X, pady=(PAD_Y_TOP, 0))
        self.instruction_text = ctk.CTkTextbox(self.root, wrap="word", height=80, corner_radius=6)
        self.instruction_text.grid(row=3, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y_INTER)

        # --- Generate Button ---
        self.generate_button = ctk.CTkButton(
            self.root, text="Generate Draft", command=self.start_generate_task, corner_radius=8
        )
        self.generate_button.grid(row=4, column=0, pady=BUTTON_PAD_Y)

        # --- Output Section ---
        generated_label = ctk.CTkLabel(self.root, text="3. Generated Draft:")
        generated_label.grid(row=5, column=0, sticky="w", padx=PAD_X, pady=(PAD_Y_TOP, 0))
        self.generated_draft_text = ctk.CTkTextbox(
            self.root, wrap="word", corner_radius=6, state="disabled"
        )
        self.generated_draft_text.grid(row=6, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y_INTER)

        # --- Button Row (Clear & Copy) ---
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.grid(row=7, column=0, pady=(0, PAD_Y_INTER))
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.clear_button = ctk.CTkButton(
            button_frame, text="Clear All", command=self.clear_all_fields,
            corner_radius=8, fg_color="#555555", hover_color="#444444"
        )
        self.clear_button.grid(row=0, column=0, padx=5)

        self.copy_button = ctk.CTkButton(
            button_frame, text="Copy Draft", command=self.copy_to_clipboard,
            corner_radius=8, fg_color="grey", hover_color="#555555"
        )
        self.copy_button.grid(row=0, column=1, padx=5)

        # --- Status Bar ---
        self.status_label = ctk.CTkLabel(self.root, text="Ready", anchor="w")
        self.status_label.grid(row=8, column=0, sticky="ew", padx=PAD_X, pady=(0, PAD_Y_INTER))

    def set_status(self, message: str):
        """Safely updates the status bar text from any thread via the queue."""
        # Use the queue to ensure thread safety if called directly from background thread
        # Though typically we'll call this from process_ui_update which is safe.
        self.status_label.configure(text=message)

    def clear_all_fields(self):
        """Clears all input and output text boxes and resets status."""
        print("Clearing fields...")
        # Temporarily enable text boxes to modify them
        self.original_msg_text.configure(state="normal")
        self.instruction_text.configure(state="normal")
        self.generated_draft_text.configure(state="normal")

        # Delete content from start ("1.0") to end ("end")
        self.original_msg_text.delete("1.0", "end")
        self.instruction_text.delete("1.0", "end")
        self.generated_draft_text.delete("1.0", "end")

        # Disable output box again
        self.generated_draft_text.configure(state="disabled")

        # Reset status bar
        self.set_status("Ready")
        # Ensure generate button is enabled if it was stuck disabled during a clear
        if self.is_generating:
             self.is_generating = False # Reset flag
             self.generate_button.configure(state="normal", text="Generate Draft")

    def copy_to_clipboard(self):
        """Copies the content of the generated draft text box to the clipboard."""
        try:
            self.generated_draft_text.configure(state="normal")
            text_to_copy = self.generated_draft_text.get("1.0", "end-1c").strip()
            self.generated_draft_text.configure(state="disabled")

            if text_to_copy and "Error:" not in text_to_copy and "Communicating" not in text_to_copy:
                # Use the root window's clipboard methods
                self.root.clipboard_clear()
                self.root.clipboard_append(text_to_copy)
                self.root.update() # Make sure it's updated
                self.set_status("Draft copied to clipboard!")
                # Reset status after a delay (2000ms = 2 seconds)
                self.root.after(2000, lambda: self.set_status("Ready"))
            elif "Error:" in text_to_copy:
                 messagebox.showwarning("Cannot Copy", "Cannot copy error messages.")
            else:
                 messagebox.showinfo("Cannot Copy", "Nothing valid generated to copy yet.")

        except Exception as e:
            error_msg = f"Could not copy text to clipboard: {e}"
            print(error_msg)
            messagebox.showerror("Clipboard Error", error_msg)
            self.set_status("Error: Failed to copy.")

    # --- Async Task Handling ---

    def start_generate_task(self):
        """
        Initiates the LLM generation task in a separate thread
        to avoid blocking the UI.
        """
        if self.is_generating:
            print("Already generating, please wait.")
            return

        original_message = self.original_msg_text.get("1.0", "end-1c").strip()
        instruction = self.instruction_text.get("1.0", "end-1c").strip()

        if not original_message or not instruction:
            messagebox.showwarning("Input Required", "Please enter both the original message and your instruction.")
            return

        # --- Prepare UI for generation ---
        self.is_generating = True
        self.generate_button.configure(state="disabled", text="Generating...")
        self.set_status("Generating draft...")
        # Clear previous output and enable for streaming updates
        self.generated_draft_text.configure(state="normal")
        self.generated_draft_text.delete("1.0", "end")
        # Leave enabled for chunks, will disable on done/error

        # --- Define Callbacks (will be called from background thread) ---
        # These callbacks put data onto the thread-safe queue
        def on_chunk_callback(chunk):
            self.ui_update_queue.put((UPDATE_CHUNK, chunk))

        def on_error_callback(error_msg):
            self.ui_update_queue.put((UPDATE_ERROR, error_msg))

        def on_done_callback():
            self.ui_update_queue.put((UPDATE_DONE, None))

        # --- Target function for the background thread ---
        def _run_async_generation():
            # This synchronous function runs in the background thread.
            # It sets up and runs the asyncio event loop just for the llm call.
            try:
                # Run the async function generate_draft_async until it completes
                asyncio.run(generate_draft_async(
                    original_message,
                    instruction,
                    on_chunk=on_chunk_callback,
                    on_error=on_error_callback,
                    on_done=on_done_callback
                    # Pass model/url if needed: model=..., ollama_url=...
                ))
            except Exception as e:
                # If asyncio.run or generate_draft_async itself fails unexpectedly
                # (though generate_draft_async has its own extensive error handling)
                error_msg = f"Error in background thread: {type(e).__name__} - {e}"
                print(error_msg)
                # Put the error on the queue so the UI thread knows about it
                self.ui_update_queue.put((UPDATE_ERROR, error_msg))

        # --- Start the Background Thread ---
        # Create a new thread to run the _run_async_generation function.
        # daemon=True ensures the thread exits when the main program exits.
        self.generation_thread = threading.Thread(target=_run_async_generation, daemon=True)
        self.generation_thread.start()


    def check_ui_queue(self):
        """
        Periodically checks the queue for updates from the background thread
        and processes them safely in the main UI thread.
        """
        try:
            # Get updates from the queue without blocking
            while True: # Process all messages currently in the queue
                update_type, data = self.ui_update_queue.get_nowait()
                self.process_ui_update(update_type, data)
        except queue.Empty:
            # If the queue is empty, do nothing this time
            pass
        finally:
            # Schedule this check to run again after 100ms
            self.root.after(100, self.check_ui_queue)

    def process_ui_update(self, update_type: str, data: any):
        """Handles updates received from the queue in the UI thread."""
        # This function runs in the main UI thread, so it's safe to update widgets.
        if update_type == UPDATE_CHUNK:
            # Append the received text chunk to the output box
            self.generated_draft_text.insert("end", data)
            self.generated_draft_text.see("end") # Auto-scroll
            # Keep status as generating while chunks arrive
            self.set_status("Generating...")
        elif update_type == UPDATE_ERROR:
            # Display the error message
            self.generated_draft_text.delete("1.0", "end") # Clear previous content
            # Make error visually distinct (optional)
            error_prefix = "Error:\n"
            self.generated_draft_text.insert("end", error_prefix + str(data))
            # Try to apply a tag for color (optional, requires defining the tag)
            # self.generated_draft_text.tag_add("error", "1.0", f"1.{len(error_prefix)}")
            # self.generated_draft_text.tag_config("error", foreground="red")

            self.set_status("Error occurred. See output box.")
            # Reset state as generation failed/stopped
            self.is_generating = False
            self.generate_button.configure(state="normal", text="Generate Draft")
            self.generated_draft_text.configure(state="disabled") # Make read-only
        elif update_type == UPDATE_DONE:
            # Generation finished successfully
            self.set_status("Draft generated successfully.")
            self.is_generating = False
            self.generate_button.configure(state="normal", text="Generate Draft")
            self.generated_draft_text.configure(state="disabled") # Make read-only


# --- Direct Execution Block ---
if __name__ == '__main__':
    root = ctk.CTk()
    app = DraftBotApp(root)
    root.mainloop()