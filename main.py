import os
import shutil
import time
import ctypes
import string
import re
import json

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

def list_drives(drives):
    print("Connected Drives:")
    for idx, (path, name) in enumerate(drives):
        print(f"{idx + 1}: {path}  -  {name}")

def pick_pico_drive(drives):
    while True:
        list_drives(drives)
        try:
            choice = int(input("Select your Pico drive by number: ")) - 1
            if 0 <= choice < len(drives):
                return drives[choice]
        except:
            pass
        print("Invalid selection. Try again.\n")

def wait_for_reconnect():
    print("\nWaiting for the Pico to reconnect...")
    initial_set = set(d[0] for d in get_drives_and_labels())
    while True:
        time.sleep(2)
        new_set = set(d[0] for d in get_drives_and_labels())
        if new_set != initial_set:
            break
    time.sleep(3)

def copy_file(src, dst):
    print(f"Copying {os.path.basename(src)} to {dst}")
    shutil.copy2(src, dst)

def copy_folder(src, dst):
    print(f"Copying contents from {src} to {dst}")
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

def payload_selection(payloads_folder, pico_path):
    base_folder = os.path.dirname(os.path.abspath(__file__))

    # Load property dictionary from external JSON file
    property_dict_path = os.path.join(base_folder, "property_dictionary.json")
    if os.path.isfile(property_dict_path):
        with open(property_dict_path, "r", encoding="utf-8") as f:
            property_dict = json.load(f)
    else:
        print("⚠️ No property_dictionary.json found. Continuing without property rules.")
        property_dict = {}

    if not os.path.isdir(payloads_folder):
        print("Payloads folder not found.")
        return

    payload_dirs = [d for d in os.listdir(payloads_folder) if os.path.isdir(os.path.join(payloads_folder, d))]
    if not payload_dirs:
        print("No premade payloads found.")
        return

    print("\nAvailable Payloads:")
    for i, name in enumerate(payload_dirs):
        print(f"{i + 1}: {name}")

    while True:
        try:
            choice = int(input("Select a payload to add by number: ")) - 1
            if 0 <= choice < len(payload_dirs):
                selected_payload = payload_dirs[choice]
                break
        except:
            pass
        print("Invalid selection. Try again.\n")

    run_choice = input(f"Do you want the '{selected_payload}' payload to run when plugged in? (y/n): ").strip().lower()
    payload_path = os.path.join(payloads_folder, selected_payload)

    # Load .cfg variable inputs
    cfg_vars = {}
    cfg_file = None
    for file in os.listdir(payload_path):
        if file.endswith(".cfg"):
            cfg_file = os.path.join(payload_path, file)
            break

    if cfg_file:
        with open(cfg_file, "r", encoding="utf-8") as f:
            content = f.read()
        var_names = set(re.findall(r"\$\$(\w+)\$\$", content))
        for var in var_names:
            user_input = input(f"Enter value for {var}: ")
            cfg_vars[var] = user_input

    # Find and load payload .txt file
    payload_txt_file = None
    for file in os.listdir(payload_path):
        if file.endswith(".txt"):
            payload_txt_file = os.path.join(payload_path, file)
            break

    if not payload_txt_file:
        print("No .txt payload file found in selected folder.")
        return

    with open(payload_txt_file, "r", encoding="utf-8") as f:
        payload_content = f.read()

    # Replace variables from .cfg
    for var, value in cfg_vars.items():
        payload_content = payload_content.replace(f"$${var}$$", value)

    # Load .prop file if available and apply modifications
    prop_file = None
    for file in os.listdir(payload_path):
        if file.endswith(".prop"):
            prop_file = os.path.join(payload_path, file)
            break

    if prop_file:
        with open(prop_file, "r", encoding="utf-8") as f:
            props = [p.strip() for p in f.read().split(",") if p.strip()]
        for prop in props:
            if prop in property_dict:
                rule = property_dict[prop]
                addition = rule.get("add", "")
                location = rule.get("location", "top").lower()
                if location == "top":
                    payload_content = addition + "\n" + payload_content
                elif location == "bottom":
                    payload_content += "\n" + addition
                
                # Check for specialMessage in the property dictionary
                special_message = rule.get("specialMessage")
                if special_message:
                    print(f"\n⚡ Special Message: {special_message}")
                    input("Press Enter to continue...")

    # Ensure path is not a root; fallback to a subfolder if needed
    if os.path.abspath(pico_path) == os.path.abspath(os.path.splitdrive(pico_path)[0] + os.sep):
        pico_path_withpayloads = os.path.join(pico_path, "payloads")
        os.makedirs(pico_path_withpayloads, exist_ok=True)

    payload_dd_path = os.path.join(pico_path, "payload.dd")

    # Create blank file if it doesn't exist
    if not os.path.exists(payload_dd_path):
        with open(payload_dd_path, "w", encoding="utf-8") as f:
            pass  # Blank file

    # Write payload content
    with open(payload_dd_path, "w", encoding="utf-8") as f:
        f.write(payload_content)



        print("✅ Payload written as payload.dd")


def is_device_finalized(drive_name, drive_path):
    required_files = ["duckyinpython.py"]
    return (
        os.path.basename(drive_name.rstrip("/\\")).upper() == "CIRCUITPY" and
        all(os.path.isfile(os.path.join(drive_path, f)) for f in required_files)
    )

def check_for_new_drive_and_delete_payload():
    while True:
        drives = get_drives_and_labels()
        for drive, name in drives:
            if name.upper() == "CIRCUITPY":
                payload_dd_path = os.path.join(drive, "payload.dd")
                duckyinpython_path = os.path.join(drive, "duckyinpython.py")

                # Wait for both files to exist
                while not (os.path.exists(payload_dd_path) and os.path.exists(duckyinpython_path)):
                    time.sleep(0.1)

                # Delete the payload and Python file
                try:
                    os.remove(payload_dd_path)
                    print(f"Deleted payload.dd from {drive}")
                except Exception as e:
                    print(f"Failed to delete payload.dd: {e}")

                try:
                    os.remove(duckyinpython_path)
                    print(f"Deleted duckyinpython.py from {drive}")
                except Exception as e:
                    print(f"Failed to delete duckyinpython.py: {e}")

                # Wait for user to unplug and replug
                print("\nUnplug the Pico, then plug it back in.")
                print("Once it's plugged in, press Enter to continue.")
                input()  # Waits silently

                # Wait until CIRCUITPY reappears
                while True:
                    time.sleep(0.1)
                    drives = get_drives_and_labels()
                    for new_drive, new_name in drives:
                        if new_name.upper() == "CIRCUITPY":
                            # Copy the file back
                            main_files_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pico", "MainFiles")
                            duckyinpython_src = os.path.join(main_files_folder, "duckyinpython.py")
                            if os.path.isfile(duckyinpython_src):
                                copy_file(duckyinpython_src, new_drive)
                                print("Copied duckyinpython.py back to the device.")
                            return  # Done


def main():
    safe_mode = input("Do you want to enable safe mode? (y/n): ").strip().lower()
    if safe_mode == "y":
        print("Safe mode enabled. Monitoring for new drives...\n")
        check_for_new_drive_and_delete_payload()
        return
    
    base_folder = os.path.dirname(os.path.abspath(__file__))
    setup_file = os.path.join(base_folder, "pico", "Setup")
    main_files_folder = os.path.join(base_folder, "pico", "MainFiles")
    payloads_folder = os.path.join(base_folder, "pico", "Payloads")

    # Step 1: Get all drives
    drives = get_drives_and_labels()
    pico_path, pico_name = pick_pico_drive(drives)

    # Step 2: Check if finalized
    if is_device_finalized(pico_name, pico_path):
        print("\n✅ Pico is already finalized. Skipping setup...\n")
    else:
        if pico_name != "CIRCUITPY":
            print("Device is not CIRCUITPY. Copying setup file to trigger reboot...")
            files = os.listdir(setup_file)
            if not files:
                print("No setup file found in pico/Setup.")
                return
            src_file = os.path.join(setup_file, files[0])
            copy_file(src_file, pico_path)
            wait_for_reconnect()
            drives = get_drives_and_labels()
            pico_path, pico_name = pick_pico_drive(drives)

        choice = input("Load BAD USB files to device? (y/n): ").strip().lower()
        if choice != "y":
            print("Aborting.")
            return

        copy_folder(main_files_folder, pico_path)
        print("BAD USB files loaded successfully.")

    # Step 3: Ask to load payload
    payload_choice = input("Do you want to add a premade payload? (y/n): ").strip().lower()
    if payload_choice != "y":
        print("Done.")
        return

    payload_selection(payloads_folder, pico_path)
    print("Process complete.")

if __name__ == "__main__":
    main()
