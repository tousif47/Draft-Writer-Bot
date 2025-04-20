# src/ui.py

# Import customtkinter library
import customtkinter as ctk
# Import standard messagebox for popups
from tkinter import messagebox
# Import the backend function we created earlier
from llm_interface import generate_draft

# --- Set Appearance ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class DraftBotApp:
    """
    Represents the main application window using CustomTkinter.
    Handles the creation, layout, and interaction of UI widgets.
    Includes functionality to generate drafts and copy them to clipboard.
    """
    def __init__(self, root):
        """
        Initializes the CustomTkinter application window.

        Args:
            root: The main customtkinter root window (ctk.CTk instance).
        """
        self.root = root
        self.root.title("Draft Writer Bot")
        self.root.minsize(550, 550) # Slightly increased min height for copy button

        # --- Configure Window Resizing ---
        # Make the main column expand
        self.root.grid_columnconfigure(0, weight=1)
        # Define row weights for vertical expansion
        self.root.grid_rowconfigure(1, weight=2) # Original message
        self.root.grid_rowconfigure(3, weight=1) # Instruction
        # Row 4 is the generate button (no weight)
        # Row 5 is the generated label (no weight)
        self.root.grid_rowconfigure(6, weight=3) # Generated draft text area
        # Row 7 is the copy button (no weight)

        # --- Create Widgets ---
        self._create_widgets()

    def _create_widgets(self):
        """
        Creates and arranges (grids) all the necessary CustomTkinter widgets.
        """
        PAD_X = 15
        PAD_Y_TOP = 15
        PAD_Y_INTER = 7

        # --- Original Message Section ---
        original_label = ctk.CTkLabel(self.root, text="1. Paste Original Message:")
        original_label.grid(row=0, column=0, sticky="w", padx=PAD_X, pady=(PAD_Y_TOP, 0))
        self.original_msg_text = ctk.CTkTextbox(self.root, wrap="word", corner_radius=6)
        self.original_msg_text.grid(row=1, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y_INTER)

        # --- Instruction Section ---
        instruction_label = ctk.CTkLabel(self.root, text="2. Your Instruction (e.g., 'Politely decline', 'Say yes'):")
        instruction_label.grid(row=2, column=0, sticky="w", padx=PAD_X, pady=(PAD_Y_TOP, 0))
        self.instruction_text = ctk.CTkTextbox(self.root, wrap="word", height=80, corner_radius=6)
        self.instruction_text.grid(row=3, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y_INTER)

        # --- Generate Button ---
        self.generate_button = ctk.CTkButton(
            self.root, text="Generate Draft",
            command=self.handle_generate_click,
            corner_radius=8
        )
        self.generate_button.grid(row=4, column=0, pady=PAD_Y_TOP)

        # --- Generated Draft Section ---
        generated_label = ctk.CTkLabel(self.root, text="3. Generated Draft:")
        generated_label.grid(row=5, column=0, sticky="w", padx=PAD_X, pady=(PAD_Y_TOP, 0))
        self.generated_draft_text = ctk.CTkTextbox(
            self.root, wrap="word", corner_radius=6, state="disabled"
        )
        self.generated_draft_text.grid(row=6, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y_INTER)

        # --- Copy Button ---
        # Add the new button specifically for copying the generated text
        self.copy_button = ctk.CTkButton(
            self.root, text="Copy Draft",
            command=self.copy_to_clipboard, # Link to the new copy method
            corner_radius=8,
            fg_color="grey", # Use a different color to distinguish it
            hover_color="#555555"
        )
        # Place it below the generated draft text area
        self.copy_button.grid(row=7, column=0, pady=(0, PAD_Y_TOP)) # Add padding below

    def handle_generate_click(self):
        """
        Handles the 'Generate Draft' button click event.
        Gets input, calls the LLM interface, and updates the UI.
        """
        original_message = self.original_msg_text.get("1.0", "end-1c").strip()
        instruction = self.instruction_text.get("1.0", "end-1c").strip()

        if not original_message or not instruction:
            messagebox.showwarning("Input Required", "Please enter both the original message and your instruction.")
            return

        # Update UI to indicate processing
        self.generate_button.configure(state="disabled", text="Generating...")
        self.generated_draft_text.configure(state="normal")
        self.generated_draft_text.delete("1.0", "end")
        self.generated_draft_text.insert("end", "Communicating with local AI... Please wait.")
        self.generated_draft_text.configure(state="disabled")
        self.root.update_idletasks() # Force UI update

        # Call the backend function
        draft_result, error_message = generate_draft(original_message, instruction)

        # Update UI with result or error
        self.generated_draft_text.configure(state="normal")
        self.generated_draft_text.delete("1.0", "end")

        if error_message:
            full_error_text = f"Error:\n{error_message}"
            self.generated_draft_text.insert("end", full_error_text)
        elif draft_result:
            self.generated_draft_text.insert("end", draft_result)
        else:
            self.generated_draft_text.insert("end", "An unexpected issue occurred.")

        self.generated_draft_text.configure(state="disabled")
        self.generate_button.configure(state="normal", text="Generate Draft")

    def copy_to_clipboard(self):
        """
        Copies the content of the generated draft text box to the system clipboard.
        """
        # Get text from the (disabled) generated draft text box
        # We need to temporarily enable it to get text in some Tkinter versions,
        # though CustomTkinter's get might work even when disabled.
        # It's safer to enable/disable.
        try:
            self.generated_draft_text.configure(state="normal")
            text_to_copy = self.generated_draft_text.get("1.0", "end-1c").strip()
            self.generated_draft_text.configure(state="disabled")

            if text_to_copy and not text_to_copy.startswith("Error:") and not text_to_copy.startswith("Communicating"):
                # Access the clipboard through the root window object (self.root)
                self.root.clipboard_clear()  # Clear the clipboard first
                self.root.clipboard_append(text_to_copy) # Append the text
                self.root.update() # Ensure the clipboard is updated system-wide

                # Optional: Give feedback to the user (e.g., change button text briefly)
                original_text = self.copy_button.cget("text")
                self.copy_button.configure(text="Copied!")
                # Schedule resetting the button text after 1.5 seconds (1500 ms)
                self.root.after(1500, lambda: self.copy_button.configure(text=original_text))

            elif text_to_copy.startswith("Error:"):
                 messagebox.showwarning("Cannot Copy", "Cannot copy error messages.")
            else:
                 messagebox.showinfo("Cannot Copy", "Nothing generated to copy yet.")

        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            messagebox.showerror("Clipboard Error", "Could not copy text to clipboard.")


# --- Direct Execution Block ---
if __name__ == '__main__':
    root = ctk.CTk()
    app = DraftBotApp(root)
    root.mainloop()