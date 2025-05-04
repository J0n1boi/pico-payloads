import os
import sys
import subprocess

def list_python_files():
    # Get the current script's filename
    script_name = os.path.basename(__file__)
    
    # Get all Python files in the current directory, excluding the script itself
    python_files = [f for f in os.listdir() if f.endswith('.py') and f != script_name]
    
    return python_files

def run_python_file(file_name):
    # Run the selected Python file
    subprocess.run(['python', file_name])

def main():
    # List available Python files
    python_files = list_python_files()
    
    if not python_files:
        print("No Python files found in the directory.")
        return

    print("Select a Python file to run:")
    
    # Display the list of Python files
    for i, file in enumerate(python_files, start=1):
        print(f"{i}. {file}")

    try:
        # Get user selection
        choice = int(input("Enter the number of the file to run: "))
        if 1 <= choice <= len(python_files):
            # Run the selected file
            selected_file = python_files[choice - 1]
            print(f"Running {selected_file}...")
            run_python_file(selected_file)
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    main()
