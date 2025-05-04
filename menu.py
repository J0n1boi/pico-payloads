import os
import subprocess

# Predefined order of Python files (case-sensitive exact filenames)
PREDEFINED_ORDER = ["main.py", "checkPayload.py", "nuke.py", "gitupload.py"]

def list_python_files():
    script_name = os.path.basename(__file__)
    all_files = [f for f in os.listdir() if f.endswith(".py") and f != script_name]

    # Files that are in the predefined list, in that order
    ordered_files = [f for f in PREDEFINED_ORDER if f in all_files]

    # Files not in the predefined list, sorted alphabetically
    remaining_files = sorted([f for f in all_files if f not in PREDEFINED_ORDER])

    return ordered_files + remaining_files

def run_python_file(file_name):
    subprocess.run(["python", file_name])

def main():
    python_files = list_python_files()
    
    if not python_files:
        print("No Python files found in the directory.")
        return

    print("Select a Python file to run:")
    for i, file in enumerate(python_files, start=1):
        print(f"{i}. {file}")

    try:
        choice = int(input("Enter the number of the file to run: "))
        if 1 <= choice <= len(python_files):
            selected_file = python_files[choice - 1]
            print(f"Running {selected_file}...")
            run_python_file(selected_file)
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    main()
