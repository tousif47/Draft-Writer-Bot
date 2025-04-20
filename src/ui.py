# src/ui.py

# Import the customtkinter library
import customtkinter as ctk
# We still need the standard messagebox for simple popups
from tkinter import messagebox

# --- We will import the backend function later when integrating ---
# from llm_interface import generate_draft

# --- Set Appearance ---
# Set the overall theme (System, Dark, Light)
ctk.set_appearance_mode("dark")
# Set the color theme (e.g., "blue", "dark-blue", "green")
ctk.set_default_color_theme("blue")


class DraftBotApp:
    """
    Represents the main application window using CustomTkinter.
    Handles the creation and layout of modern UI widgets.
    """
    def __init__(self, root):
        """
        Initializes the CustomTkinter application window.

        Args:
            root: The main customtkinter root window (ctk.CTk instance).
        """
        self.root = root
        self.root.title("Draft Writer Bot")
        self.root.minsize(550, 500) # Set a minimum size

        # --- Configure Window Resizing ---
        # Allow the main column (column 0) to expand horizontally
        self.root.grid_columnconfigure(0, weight=1)
        # Allow specific rows containing text boxes to expand vertically
        self.root.grid_rowconfigure(1, weight=2) # Original message
        self.root.grid_rowconfigure(3, weight=1) # Instruction
        self.root.grid_rowconfigure(6, weight=3) # Generated draft

        # --- Create Widgets ---
        self._create_widgets()

    def _create_widgets(self):
        """
        Creates and arranges (grids) all the necessary CustomTkinter widgets.
        """
        # Padding constants for layout
        PAD_X = 15
        PAD_Y_TOP = 15
        PAD_Y_INTER = 7

        # --- Original Message Section ---
        # Use CTkLabel for themed labels
        original_label = ctk.CTkLabel(self.root, text="1. Paste Original Message:")
        original_label.grid(row=0, column=0, sticky="w", padx=PAD_X, pady=(PAD_Y_TOP, 0))

        # Use CTkTextbox for themed, scrollable text areas
        self.original_msg_text = ctk.CTkTextbox(
            self.root, wrap="word", # Wrap text by word
            # Height is controlled by grid weights/window size, not lines
            # Set corner radius for rounded corners
            corner_radius=6
            # border_width=1 # Optional border
        )
        # Place using grid, sticky="nsew" makes it fill the cell on resize
        self.original_msg_text.grid(row=1, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y_INTER)

        # --- Instruction Section ---
        instruction_label = ctk.CTkLabel(self.root, text="2. Your Instruction (e.g., 'Politely decline', 'Say yes'):")
        instruction_label.grid(row=2, column=0, sticky="w", padx=PAD_X, pady=(PAD_Y_TOP, 0))

        self.instruction_text = ctk.CTkTextbox(
            self.root, wrap="word", height=80, # Can set an initial pixel height
            corner_radius=6
        )
        self.instruction_text.grid(row=3, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y_INTER)

        # --- Generate Button ---
        # Use CTkButton for themed buttons
        self.generate_button = ctk.CTkButton(
            self.root, text="Generate Draft",
            command=self.handle_generate_click, # Method to call on click
            corner_radius=8
        )
        self.generate_button.grid(row=4, column=0, pady=PAD_Y_TOP) # Centered by default

        # --- Generated Draft Section ---
        generated_label = ctk.CTkLabel(self.root, text="3. Generated Draft:")
        generated_label.grid(row=5, column=0, sticky="w", padx=PAD_X, pady=(PAD_Y_TOP, 0))

        self.generated_draft_text = ctk.CTkTextbox(
            self.root, wrap="word",
            corner_radius=6,
            state="disabled" # Make it read-only initially
        )
        self.generated_draft_text.grid(row=6, column=0, sticky="nsew", padx=PAD_X, pady=(PAD_Y_INTER, PAD_Y_TOP))

    def handle_generate_click(self):
        """
        Placeholder method called when the 'Generate Draft' button is clicked.
        Will be updated later to call the llm_interface.
        """
        # Get text from CTkTextbox widgets
        # Use "1.0" for start, "end-1c" to exclude the automatic newline
        original_message = self.original_msg_text.get("1.0", "end-1c").strip()
        instruction = self.instruction_text.get("1.0", "end-1c").strip()

        # Basic validation
        if not original_message or not instruction:
            # Using standard tkinter messagebox for simplicity for now
            messagebox.showwarning("Input Required", "Please enter both the original message and your instruction.")
            return

        # --- Placeholder Action ---
        print("--- Generate Button Clicked (CustomTkinter) ---")
        print(f"Original: '{original_message}'")
        print(f"Instruction: '{instruction}'")
        print("---------------------------------------------")

        # --- TODO: Integration Step ---
        # (Similar to before, but using CTkTextbox methods)
        # 1. Import generate_draft from llm_interface
        # 2. Disable button, configure output box state to normal, delete old text, insert "Generating..."
        # 3. Call: draft, error = generate_draft(original_message, instruction)
        # 4. Configure output box state to normal, delete "Generating...", insert result or error
        # 5. Configure output box state back to disabled, enable button

        # Example of updating CTkTextbox later:
        # self.generated_draft_text.configure(state="normal") # Enable writing
        # self.generated_draft_text.delete("1.0", "end")     # Clear previous content
        # self.generated_draft_text.insert("end", "This is where the generated draft will go.")
        # self.generated_draft_text.configure(state="disabled") # Disable writing again


# --- Direct Execution Block ---
# Allows running `python src/ui.py` to preview the UI
if __name__ == '__main__':
    # Use ctk.CTk() instead of tk.Tk()
    root = ctk.CTk()
    app = DraftBotApp(root)
    # Start the event loop (same as tkinter)
    root.mainloop()