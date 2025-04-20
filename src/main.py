# src/main.py

# Import customtkinter instead of tkinter
import customtkinter as ctk
# Import our application window class from the ui module (ui.py file)
from ui import DraftBotApp

# The __name__ == "__main__" block ensures this code only runs
# when this script is executed directly.
if __name__ == "__main__":
    # 1. Create the main root window using customtkinter.
    root = ctk.CTk()

    # 2. Create an instance of our application class (defined in ui.py),
    #    passing the customtkinter root window to it.
    app = DraftBotApp(root)

    # 3. Start the tkinter event loop (customtkinter uses the same loop).
    #    This makes the window visible and interactive.
    root.mainloop()