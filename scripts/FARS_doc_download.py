import os
import requests

# Define the target directory for downloads
target_dir = os.path.join("..", "docs", "research")
os.makedirs(target_dir, exist_ok=True)

# Path for the error log file
error_log_path = os.path.join(target_dir, "download_errors.txt")

# List of file URLs to download
file_urls = [
    "https://static.nhtsa.gov/nhtsa/downloads/FARS/1975/Release%20Notes%201975-1981.txt",
    "https://static.nhtsa.gov/nhtsa/downloads/FARS/1982/FARS%201982-1988%201990-2000%20Release%20Note.txt",
    "https://static.nhtsa.gov/nhtsa/downloads/FARS/1989/FARS1989%20Release%20Note.txt",
    "https://static.nhtsa.gov/nhtsa/downloads/FARS/2001/FARS2001-2009%20Release%20Note.txt",
    "https://static.nhtsa.gov/nhtsa/downloads/FARS/2001/DRUNK_DR%20CORRECTION/Drunk_dr%20correction.docx",
    "https://static.nhtsa.gov/nhtsa/downloads/FARS/2009/FARS2009%20Release%20Notes.txt",
    "https://static.nhtsa.gov/nhtsa/downloads/FARS/2010/FARS2010%20Release%20Notes.txt",
    "https://static.nhtsa.gov/nhtsa/downloads/FARS/2011/FARS2011%20Release%20Notes.txt",
    "https://static.nhtsa.gov/nhtsa/downloads/FARS/2022/FARS2022%20Release%20Notes.txt",
    "https://static.nhtsa.gov/nhtsa/downloads/FARS/Auxiliary_FARS_Files_Formats/Auxiliary%20Format%20File%20Release%20Notes.txt",
    "https://static.nhtsa.gov/nhtsa/downloads/FARS/FARS-GES%20Standardization/2009%20FARS-GES%20Standardization.pdf",
    "https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813556",
    "https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813545",
    "https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813546",
    "https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813547"
]

# Add files for years 2009 to 2022
for year in range(2009, 2023):
    file_urls.append(f"https://static.nhtsa.gov/nhtsa/downloads/FARS/{year}/FARS{year}%20Release%20Notes.txt")

# Function to download a file
def download_file(url, target_folder):
    local_filename = os.path.join(target_folder, url.split("/")[-1])
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an error for bad status codes
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {local_filename}")
    except requests.RequestException as e:
        print(f"Failed to download {url}: {e}")
        # Log the error to a file
        with open(error_log_path, "a") as error_log:
            error_log.write(f"Failed to download {url}: {e}\n")

# Download all files
for file_url in file_urls:
    download_file(file_url, target_dir)