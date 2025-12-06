import os
import shutil
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime

# Folder containing the HTML files
PAGES_FOLDER = r"C:/LOCAL_PROJECTS/RRR_LOGS/pages"
SOURCE_FOLDER = os.path.expanduser("~/Downloads/pages")
BACKUP_ROOT =os.path.expanduser("~/Downloads/backups")


def backup_pages_folder(source_folder, backup_root):
    # Create timestamp suffix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = os.path.join(backup_root, f"pages_{timestamp}")
    
    # Create backup directory
    os.makedirs(backup_folder, exist_ok=True)
    
    # Copy all contents of pages folder into the timestamped backup
    shutil.copytree(source_folder, backup_folder, dirs_exist_ok=True)
    
    print(f"✅ Backup completed: {backup_folder}")
    return backup_folder


def copy_pages():
    src_dir = os.path.expanduser(SOURCE_FOLDER)
    dst_dir = PAGES_FOLDER

    os.makedirs(dst_dir, exist_ok=True)

    for file in os.listdir(src_dir):
        if file.endswith(".html"):
            src_path = os.path.join(src_dir, file)
            dst_path = os.path.join(dst_dir, file)
            shutil.copy2(src_path, dst_path)
            print(f"Copied: {file}")


def count_filtered_pages(folder):
    count = 0
    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)
        if (
            os.path.isfile(file_path)
            and file_name.lower().startswith("property")
            and file_name.lower().endswith((".html", ".htm"))
        ):
            count += 1
    print(f"📄 {count} filtered files found in: {folder}")
    return count


def do_scrape_listings():
    backup_pages_folder(SOURCE_FOLDER, BACKUP_ROOT)
    copy_pages()
    rename_files_in_folder(PAGES_FOLDER)
    remove_non_property_files(PAGES_FOLDER)
    page_count = count_filtered_pages(PAGES_FOLDER)
    return page_count


def remove_files_in_directory(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Could not delete {file_path}: {e}")


def remove_non_property_files(folder):
    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)

        # Skip folders and only process files
        if not os.path.isfile(file_path):
            continue

        # Check if filename starts with "property" (case-insensitive)
        if not file_name.lower().startswith("property"):
            print(f"Deleting: {file_name}")
            os.remove(file_path)


def rename_files_in_folder(folder):
    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)
        if not os.path.isfile(file_path) or not file_name.lower().endswith((".html", ".htm")):
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f, "html.parser")

            canonical_tag = soup.find("link", rel="canonical")
            if not canonical_tag or not canonical_tag.has_attr("href"):
                print(f"Skipping {file_name} (no canonical link)")
                continue

            canonical_url = canonical_tag["href"]
            if not canonical_url.startswith("https://www.homes.com/property/"):
                print(f"Skipping {file_name} (unexpected URL format)")
                continue

            slug = canonical_url.replace("https://www.homes.com/property/", "property_").strip("/")
            new_file_name = slug.replace("/", "_") + ".html"
            new_file_path = os.path.join(folder, new_file_name)

            if os.path.exists(new_file_path):
                print(f"Conflict: {new_file_name} already exists. Skipping.")
                continue

            os.rename(file_path, new_file_path)
            print(f"Renamed: {file_name} -> {new_file_name}")

        except PermissionError as e:
            print(f"PermissionError on {file_name}: {e}. File may be open in another program.")
        except Exception as e:
            print(f"Error processing {file_name}: {e}")


def main():
    do_scrape_listings()


if __name__ == "__main__":
    main()

