import os
import shutil
import ctypes
import string

# Function to get drives and their labels on Windows
def get_drives_and_labels():
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drive_path = letter + ":\\"
            try:
                volume_name = ctypes.create_unicode_buffer(1024)
                fs_name = ctypes.create_unicode_buffer(1024)
                ctypes.windll.kernel32.GetVolumeInformationW(
                    ctypes.c_wchar_p(drive_path),
                    volume_name,
                    ctypes.sizeof(volume_name),
                    None,
                    None,
                    None,
                    fs_name,
                    ctypes.sizeof(fs_name)
                )
                drives.append((drive_path, volume_name.value))
            except:
                drives.append((drive_path, "Unknown"))
        bitmask >>= 1
    return drives

# Function to list all connected drives
def list_drives(drives):
    if not drives:
        print("No drives found.")
    else:
        for i, (drive, name) in enumerate(drives):
            print(f"{i + 1}. Drive: {drive}, Name: {name}")
    return drives

# Function to prompt user for selection of drive
def select_drive(drives):
    selected = None
    while selected is None:
        try:
            selection = int(input("Select the number of the drive you want to nuke: "))
            if 1 <= selection <= len(drives):
                selected = drives[selection - 1][0]  # Get the drive path
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    return selected

# Function to handle copying files
def copy_file(src, dst):
    print(f"Copying {os.path.basename(src)} to {dst}")
    try:
        shutil.copy2(src, dst)
    except PermissionError:
        print(f"Permission denied while copying to {dst}. Skipping this drive.")
    except Exception as e:
        print(f"An error occurred while copying to {dst}: {e}")

# Function to handle the process if the selected drive is CIRCUITPY
def handle_circuitpy(selected_drive, drives):
    while True:
        # Verify that the selected drive name is CIRCUITPY
        selected_drive_name = [name for drive, name in drives if drive == selected_drive]

        if selected_drive_name and "CIRCUITPY" in selected_drive_name[0]:
            print("Please unplug the device, press and hold the BOOTSEL button, and plug the device back in while holding the button.")
            input("Press Enter when the device is reconnected...")

            # Check if the device is still CIRCUITPY
            new_drives = get_drives_and_labels()
            new_selected_drive_name = [name for drive, name in new_drives if drive == selected_drive]
            
            if new_selected_drive_name and "CIRCUITPY" in new_selected_drive_name[0]:
                print("Device still in CIRCUITPY mode. Restarting process...")
                continue
            else:
                print("Device reconnected with a new name, preparing to copy the Nuke file.")
                
                # Define base folder and the Nuke folder
                base_folder = os.path.dirname(os.path.abspath(__file__))
                nuke_folder_path = os.path.join(base_folder, "pico", "Nuke")
                
                # Find the .uf2 file inside the Nuke folder
                nuke_file_path = next((os.path.join(nuke_folder_path, f) for f in os.listdir(nuke_folder_path) if f.endswith('.uf2')), None)
                
                if nuke_file_path:
                    copy_file(nuke_file_path, selected_drive)  # Copy to the selected drive
                
                input("Press Enter when the device is reconnected...")
                new_drives = get_drives_and_labels()

                # Check if the device has been renamed
                if any("CIRCUITPY" not in name for _, name in new_drives):
                    print("Nuke file was successfully copied and device renamed.")
                    break
                else:
                    print("Device still in CIRCUITPY mode. Restarting process...")
                    continue

        else:
            print(f"Drive name {selected_drive} is not CIRCUITPY, restarting process...")
            break

# Main function to execute the process
def main():
    drives = get_drives_and_labels()

    if not drives:
        print("No drives detected. Exiting.")
        return

    list_drives(drives)
    selected_drive = select_drive(drives)
    print(f"Selected drive: {selected_drive}")

    handle_circuitpy(selected_drive, drives)
    
    # If the process completed successfully, copy the Setup file (from the folder)
    base_folder = os.path.dirname(os.path.abspath(__file__))
    setup_folder_path = os.path.join(base_folder, "pico", "Setup")
    
    # Find the .uf2 file inside the Setup folder
    setup_file_path = next((os.path.join(setup_folder_path, f) for f in os.listdir(setup_folder_path) if f.endswith('.uf2')), None)
    if setup_file_path:
        copy_file(setup_file_path, selected_drive)

    input("Press Enter when the device is reconnected...")

    # Final check for CIRCUITPY and duckyinpython.py file
    drives = get_drives_and_labels()  # Only check once more
    if any("CIRCUITPY" in name for _, name in drives):
        for drive, name in drives:
            if "CIRCUITPY" in name:
                if not os.path.exists(os.path.join(drive, "duckyinpython.py")):
                    print("Nuke was successful!")
                    break
                else:
                    print("File duckyinpython.py exists. Restarting process...")
                    main()
                    break
    else:
        print("Device not found in CIRCUITPY mode. Restarting process...")
        main()

if __name__ == "__main__":
    main()
