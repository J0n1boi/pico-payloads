import os
import time
import json
import re

def get_current_drives():
    if os.name == "nt":
        from string import ascii_uppercase
        return [f"{d}:/" for d in ascii_uppercase if os.path.exists(f"{d}:/")]
    else:
        return [f"/media/{user}/{d}" for user in os.listdir("/media") for d in os.listdir(f"/media/{user}")]

def wait_for_device_and_find_dd():
    print("🔌 Please plug in the device...")
    scanned = set()
    while True:
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:/"
            dd_path = os.path.join(drive, "payload.dd")
            if os.path.exists(dd_path) and drive not in scanned:
                print(f"📦 Found payload.dd on {drive}")
                return drive, dd_path
        time.sleep(1)


def clean_first_line(dd_path):
    with open(dd_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    if not lines:
        print("⚠️ .dd file is empty.")
        return ""

    first_line = lines[0].strip()

    if first_line.upper().startswith("REM "):
        payload_name = first_line[4:].strip()
    else:
        payload_name = first_line.strip()

    print(f"💬 Payload identified: '{payload_name}'")
    return payload_name


def delete_files(device_path):
    for filename in ["payload.dd", "duckytopython.py"]:
        try:
            os.remove(os.path.join(device_path, filename))
            print(f"🗑️ Deleted {filename}")
        except:
            pass

def payload_selection(payload_name, payloads_folder, pico_path):
    base_folder = os.path.dirname(os.path.abspath(__file__))
    property_dict_path = os.path.join(base_folder, "property_dictionary.json")
    if os.path.isfile(property_dict_path):
        with open(property_dict_path, "r", encoding="utf-8") as f:
            property_dict = json.load(f)
    else:
        print("⚠️ No property_dictionary.json found.")
        property_dict = {}

    payload_path = os.path.join(payloads_folder, payload_name)
    if not os.path.isdir(payload_path):
        print(f"❌ Payload folder '{payload_name}' not found.")
        return

    run_choice = input(f"Do you want the '{payload_name}' payload to be re-added? (y/n): ").strip().lower()
    if run_choice != "y":
        return

    # Handle .cfg
    cfg_vars = {}
    cfg_file = next((f for f in os.listdir(payload_path) if f.endswith(".cfg")), None)
    if cfg_file:
        with open(os.path.join(payload_path, cfg_file), "r", encoding="utf-8") as f:
            content = f.read()
        var_names = set(re.findall(r"\$\$(\w+)\$\$", content))
        for var in var_names:
            user_input = input(f"Enter value for {var}: ")
            cfg_vars[var] = user_input

    # Load .txt
    txt_file = next((f for f in os.listdir(payload_path) if f.endswith(".txt")), None)
    if not txt_file:
        print("❌ No .txt payload found.")
        return

    with open(os.path.join(payload_path, txt_file), "r", encoding="utf-8") as f:
        payload_content = f.read()
    for var, value in cfg_vars.items():
        payload_content = payload_content.replace(f"$${var}$$", value)

    # Handle .prop
    prop_file = next((f for f in os.listdir(payload_path) if f.endswith(".prop")), None)
    if prop_file:
        with open(os.path.join(payload_path, prop_file), "r", encoding="utf-8") as f:
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
                if "specialMessage" in rule:
                    print(f"⚡ Special Message: {rule['specialMessage']}")
                    input("Press Enter to continue...")

    # Save result
    payload_dd_path = os.path.join(pico_path, "payload.dd")
    with open(payload_dd_path, "w", encoding="utf-8") as f:
        f.write(payload_content)
    print("✅ Payload written back as payload.dd")

def main():
    device_path, dd_path = wait_for_device_and_find_dd()
    payload_name = clean_first_line(dd_path)
    delete_files(device_path)

    time.sleep(3)
    user_response = input(f"Do you want to load the '{payload_name}' payload? (y/n): ").strip().lower()
    if user_response == "y":
        pico_path = device_path
        payloads_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pico", "Payloads")
        payload_selection(payload_name, payloads_folder, pico_path)

if __name__ == "__main__":
    main()
