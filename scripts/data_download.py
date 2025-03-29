import requests
import os
import time
from urllib.parse import urljoin

def download_file(url, output_dir):
    """
    Downloads a file from a URL to the specified output directory.
    
    Args:
        url (str): URL of the file to download
        output_dir (str): Directory where the file will be saved
    
    Returns:
        str: Path to the downloaded file or None if the download failed
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the filename from the URL
    filename = url.split('/')[-1]
    output_path = os.path.join(output_dir, filename)
    
    # Check if the file already exists
    if os.path.exists(output_path):
        print(f"File {filename} already exists in {output_dir}, skipping download.")
        return output_path
    
    try:
        print(f"Downloading {filename} from {url}...")
        
        # Download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Save the file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"Successfully downloaded {filename} to {output_dir}")
        return output_path
    
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None

def download_fars_data(years, base_dir="data/raw"):
    """
    Downloads FARS data for the specified years.
    
    Args:
        years (list): List of years to download data for
        base_dir (str): Base directory to save downloaded files
    """
    base_url = "https://static.nhtsa.gov/nhtsa/downloads/FARS/"
    
    for year in years:
        year_str = str(year)
        
        # Construct the URL for the year's National CSV file
        file_url = urljoin(base_url, f"{year_str}/National/FARS{year_str}NationalCSV.zip")
        
        # Create year-specific output directory
        year_dir = os.path.join(base_dir, year_str)
        
        # Download the file
        print(f"\nProcessing year {year_str}...")
        downloaded_file = download_file(file_url, year_dir)
        
        if downloaded_file:
            print(f"FARS data for {year_str} downloaded successfully.")
        else:
            print(f"Failed to download FARS data for {year_str}.")
        
        # Add a small delay to avoid overwhelming the server
        time.sleep(1)

if __name__ == "__main__":
    # Years to download
    years_to_download = range(1975, 2023)  # From 1975 to 2022
    
    # Ensure path separators are correct for the operating system
    base_dir = os.path.join("data", "raw")
    
    # Download data
    download_fars_data(years_to_download, base_dir)
    
    print("\nDownload process completed.")