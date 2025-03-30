#!/usr/bin/env python3
import os
import requests
import sys
import time

# Create the destination directory if it doesn't exist
os.makedirs('docs/research', exist_ok=True)

def download_file(url, output_path):
    """
    Download a file and save it to the specified path with a simple progress indicator
    """
    try:
        print(f"Downloading: {url}")
        
        # Make the request with stream=True to download in chunks
        response = requests.get(url, stream=True, allow_redirects=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Get total file size if available
        total_size = int(response.headers.get('content-length', 0))
        
        # Simple progress tracking
        downloaded = 0
        start_time = time.time()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    size = f.write(chunk)
                    downloaded += size
                    
                    # Update progress
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        bar_length = 30
                        filled_length = int(bar_length * downloaded // total_size)
                        bar = '█' * filled_length + '░' * (bar_length - filled_length)
                        
                        # Calculate speed
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            speed = downloaded / (1024 * elapsed)  # KB/s
                            
                            # Print progress bar
                            sys.stdout.write(f"\r[{bar}] {percent:.1f}% ({downloaded/1024:.1f}/{total_size/1024:.1f} KB) {speed:.1f} KB/s")
                            sys.stdout.flush()
                    else:
                        # If total size is unknown, just show downloaded amount
                        sys.stdout.write(f"\rDownloaded: {downloaded/1024:.1f} KB")
                        sys.stdout.flush()
        
        print(f"\n✓ Downloaded: {output_path}")
        return True
    except Exception as e:
        print(f"\n❌ Failed to download: {url}")
        print(f"Error: {e}")
        return False

# List of URLs and their corresponding output filenames
files_to_download = [
    ("https://static.nhtsa.gov/nhtsa/downloads/FARS/1975/Release%20Notes%201975-1981.txt", "docs/research/Release_Notes_1975-1981.txt"),
    ("https://static.nhtsa.gov/nhtsa/downloads/FARS/1982/FARS%201982-1988%201990-2000%20Release%20Note.txt", "docs/research/FARS_1982-1988_1990-2000_Release_Note.txt"),
    ("https://static.nhtsa.gov/nhtsa/downloads/FARS/1989/FARS1989%20Release%20Note.txt", "docs/research/FARS1989_Release_Note.txt"),
    ("https://static.nhtsa.gov/nhtsa/downloads/FARS/2001/FARS2001-2009%20Release%20Note.txt", "docs/research/FARS2001-2009_Release_Note.txt"),
    ("https://static.nhtsa.gov/nhtsa/downloads/FARS/2001/DRUNK_DR%20CORRECTION/Drunk_dr%20correction.docx", "docs/research/Drunk_dr_correction.docx"),
    ("https://static.nhtsa.gov/nhtsa/downloads/FARS/2009/FARS2009%20Release%20Notes.txt", "docs/research/FARS2009_Release_Notes.txt"),
    ("https://static.nhtsa.gov/nhtsa/downloads/FARS/2010/FARS2010%20Release%20Notes.txt", "docs/research/FARS2010_Release_Notes.txt"),
    ("https://static.nhtsa.gov/nhtsa/downloads/FARS/2011/FARS2011%20Release%20Notes.txt", "docs/research/FARS2011_Release_Notes.txt"),
    ("https://static.nhtsa.gov/nhtsa/downloads/FARS/Auxiliary_FARS_Files_Formats/Auxiliary%20Format%20File%20Release%20Notes.txt", "docs/research/Auxiliary_Format_File_Release_Notes.txt"),
    ("https://static.nhtsa.gov/nhtsa/downloads/FARS/FARS-GES%20Standardization/2009%20FARS-GES%20Standardization.pdf", "docs/research/2009_FARS-GES_Standardization.pdf"),
    ("https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813556", "docs/research/NHTSA_Publication_813556.pdf"),
    ("https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813545", "docs/research/NHTSA_Publication_813545.pdf"),
    ("https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813546", "docs/research/NHTSA_Publication_813546.pdf"),
    ("https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813547", "docs/research/NHTSA_Publication_813547.pdf"),
]

# Add annual release notes from 2012-2022
for year in range(2012, 2023):
    url = f"https://static.nhtsa.gov/nhtsa/downloads/FARS/{year}/FARS{year}%20Release%20Notes.txt"
    output_path = f"docs/research/FARS{year}_Release_Notes.txt"
    files_to_download.append((url, output_path))

# Download all files
successful_downloads = 0
total_files = len(files_to_download)

print(f"Starting download of {total_files} files to docs/research/")
print("-" * 60)

for url, output_path in files_to_download:
    if download_file(url, output_path):
        successful_downloads += 1

print(f"\nDownload summary: {successful_downloads}/{total_files} files downloaded successfully.")