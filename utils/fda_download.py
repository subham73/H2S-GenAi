import requests
import os

# Endpoint for FDA's download metadata
DOWNLOAD_METADATA_URL = "https://api.fda.gov/download.json"

# Directory to save the downloads
SAVE_DIR = "fda_medical_device_2025"
os.makedirs(SAVE_DIR, exist_ok=True)

def is_2025_partition(partition):
    # Checks if the partition is clearly a 2025 dataset (by filename or export_date)
    for key in ['file', 'display_name']:
        if key in partition and '2025' in partition[key]:
            return True
    return False

def get_medical_device_partitions():
    resp = requests.get(DOWNLOAD_METADATA_URL)
    data = resp.json()
    partitions = []

    # Find all medical device-related sections (like device, enforcement, registration, etc.)
    devices_section = data.get('results', {}).get('device', {})
    for key, section in devices_section.items():
        if 'partitions' in section:
            for pt in section['partitions']:
                if is_2025_partition(pt):
                    partitions.append({
                        "file": pt["file"],
                        "display_name": pt.get("display_name", ""),
                        "size_mb": pt.get("size_mb", ""),
                        "records": pt.get("records", ""),
                        "section": key
                    })
    return partitions

def download_partitions(partitions):
    for pt in partitions:
        fname = os.path.join(SAVE_DIR, os.path.basename(pt['file']))
        print(f"Downloading {pt['display_name']} ({pt['file']}) ...")
        r = requests.get(pt['file'], stream=True)
        with open(fname, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Saved to {fname} [{pt['size_mb']} MB, {pt['records']} records]")

def main():
    partitions = get_medical_device_partitions()
    if not partitions:
        print("No 2025 medical device data found.")
        return
    print(f"Found {len(partitions)} 2025 medical device datasets. Starting download...")
    download_partitions(partitions)

if __name__ == "__main__":
    main()
