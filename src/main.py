# src/main.py

import customtkinter as ctk

from ui import DraftBotApp

# Define a main function that sets up and runs the app
def main():
    """Initializes and runs the Draft Writer Bot application."""
    root = ctk.CTk()
    app = DraftBotApp(root)
    root.mainloop()

# This block now calls the main function when the script is run directly
if __name__ == "__main__":
    main()