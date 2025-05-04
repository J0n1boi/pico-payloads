import os
import requests
import shutil

repo_api_url = "https://api.github.com/repos/J0n1boi/pico-payloads/contents"
temp_repo_dir = "__temp_repo"

def fetch_file_list(api_url):
    response = requests.get(api_url)
    if response.status_code != 200:
        print(f"Failed to fetch: {api_url}")
        return []

    data = response.json()
    files = []

    for item in data:
        if item["type"] == "file" and item.get("download_url"):
            files.append({
                "name": item["name"],
                "download_url": item["download_url"],
                "path": item["path"]
            })
        elif item["type"] == "dir":
            files.extend(fetch_file_list(item["url"]))  # Recurse into subfolders

    return files

def download_files(files):
    for file in files:
        local_path = os.path.join(temp_repo_dir, file["path"])
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        response = requests.get(file["download_url"])
        with open(local_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {file['path']}")

def delete_non_python_and_temp():
    current_script = os.path.basename(__file__)
    for item in os.listdir():
        if item in [current_script, temp_repo_dir]:
            continue
        if os.path.isfile(item):
            os.remove(item)
            print(f"Deleted: {item}")
        elif os.path.isdir(item):
            if item.startswith("."):
                print(f"Skipped hidden/system folder: {item}")
                continue
            try:
                shutil.rmtree(item)
                print(f"Deleted folder: {item}")
            except PermissionError as e:
                print(f"Permission denied when deleting: {item} -> {e}")

def copy_from_temp_to_main():
    for root, _, files in os.walk(temp_repo_dir):
        for file in files:
            src = os.path.join(root, file)
            rel_path = os.path.relpath(src, temp_repo_dir)
            dst = os.path.join(".", rel_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            print(f"Copied: {rel_path}")

def main():
    files = fetch_file_list(repo_api_url)
    if not files:
        print("No downloadable files found in the repository.")
        return

    print("Files to be downloaded:")
    for file in files:
        print(" -", file["path"])

    input("\nPress Enter to proceed with downloading files...")

    os.makedirs(temp_repo_dir, exist_ok=True)
    download_files(files)

    print("\n⚠️ WARNING: You are about to delete everything in this folder (except this script and '__temp_repo').")
    print("This could be fatal if you're not careful. Review the folder now if you're unsure.")
    input("Press Enter to confirm and delete...")

    delete_non_python_and_temp()

    print("\n✔️ Deletion complete. About to move the new files into place.")
    input("Press Enter to continue...")

    copy_from_temp_to_main()
    shutil.rmtree(temp_repo_dir)

    print("\n✅ All operations completed.")
    print("📝 It's recommended you skim through the files to ensure nothing is corrupted or missing.")

if __name__ == "__main__":
    main()
