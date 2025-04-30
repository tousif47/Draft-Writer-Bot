# setup.py

# Import necessary functions from setuptools
import setuptools
import os

# --- Helper function to read the README file ---
def read_readme():
    """Reads the README.md file for the long description."""
    try:
        # Get the absolute path to the directory containing setup.py
        here = os.path.abspath(os.path.dirname(__file__))

        # Construct the full path to README.md
        readme_path = os.path.join(here, 'README.md')

        # Open and read the file with UTF-8 encoding
        with open(readme_path, encoding='utf-8') as f:
            return f.read()
        
    except FileNotFoundError:
        # Fallback if README.md is missing
        print("Warning: README.md not found. Long description will be empty.")
        return ""

# --- Package Configuration ---
setuptools.setup(
    # --- Basic Information ---
    # The name of your package as it will appear on PyPI.
    # Should be unique. Use hyphens for word separation.
    name="draft-writer-bot",

    # The current version of your package.
    # Follow semantic versioning (e.g., MAJOR.MINOR.PATCH -> 0.1.0).
    # Increment this each time you upload a new version.
    version="1.0.0", # Start with an initial development version

    author="Muhammad Tousif Zaman",
    author_email="mtzaman94@gmail.com",

    # A short, one-sentence description of your package.
    description="A simple desktop AI assistant for drafting message replies using local LLMs via Ollama.",

    # --- Detailed Description ---
    # A longer description read from your README.md file.
    # This will be displayed on the PyPI project page.
    long_description=read_readme(),

    # Specifies the format of the long description (Markdown in this case).
    long_description_content_type="text/markdown",

    # --- Project URLs ---
    url="https://github.com/tousif47/Draft-Writer-Bot",

    # Optional: Add other relevant URLs, like documentation or issue tracker.
    project_urls={
        "Bug Tracker": "https://github.com/tousif47/Draft-Writer-Bot/issues",
    },

    # --- Build Configuration ---
    # Specifies the directory containing the package source code relative to setup.py.
    # Since our code is in 'src/', we set the base to the current directory ('').
    package_dir={'': 'src'},

    # Automatically find all packages within the specified package_dir ('src/').
    # It will find the 'DraftWriterBot' implicitly if you structure imports correctly,
    # but explicitly finding packages under 'src' is cleaner.
    # It looks for folders containing an __init__.py file.
    # We don't have sub-packages here, but find_packages handles the root 'src' content.
    packages=setuptools.find_packages(where='src'),

    # --- Dependencies ---
    # List of external packages required for your application to run.
    # These will be automatically installed by pip when your package is installed.
    # Match the versions if necessary, but usually just listing names is fine.
    install_requires=[
        "customtkinter>=5.2.0",
        "httpx>=0.27.0",
        "requests",
    ],

    # --- Python Version Requirement ---
    # Specifies the minimum Python version required.
    # Align this with the version you developed and tested with.
    python_requires=">=3.9",

    # --- Entry Points (for command-line execution) ---
    # Defines commands that should be created when the package is installed.
    # This allows users to run the app directly from the terminal.
    entry_points={
        # 'console_scripts' creates executable scripts.
        'console_scripts': [
            # Format: 'command_name = module_path:function_name'
            # This creates a command 'draft-writer-bot' that runs the main function
            # from the 'main' module inside the package.
            # We need a main() function in src/main.py for this to work.
            'draft-writer-bot=main:main', # Assumes a main() function in src/main.py
        ],
        # 'gui_scripts' is similar but intended for GUI apps on Windows,
        # preventing a console window from opening. Often used alongside console_scripts.
        'gui_scripts': [
             'draft-writer-bot-gui=main:main', # Can use the same entry point function
        ]
    },

    # --- Classifiers (Metadata for PyPI) ---
    # Helps users find your package on PyPI and indicates its status/audience.
    # Choose appropriate classifiers from https://pypi.org/classifiers/
    classifiers=[
        # Development Status
        "Development Status :: 4 - Beta", # Or 4 - Beta, 5 - Production/Stable

        # Intended Audience
        "Intended Audience :: End Users/Desktop",

        # Topics
        "Topic :: Communications :: Chat",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Utilities",

        # License
        "License :: OSI Approved :: MIT License",

        # Supported Python Versions
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",

        # Operating System
        "Operating System :: Microsoft :: Windows",

        # Environment
        "Environment :: Win32 (MS Windows)",
    ],
)