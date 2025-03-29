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
        
        # Special case: Fix the incorrect filename for 1996 Auxiliary CSV
        if "1996" in url and "AuxiliaryCVS.zip" in filename:
            corrected_filename = filename.replace("CVS", "CSV")
            corrected_output_path = os.path.join(output_dir, corrected_filename)
            os.rename(output_path, corrected_output_path)
            print(f"Renamed {filename} to {corrected_filename}")
            return corrected_output_path
        
        return output_path
    
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        
        # Log the error to a file
        error_log_dir = os.path.join("data", "raw", "errors")
        os.makedirs(error_log_dir, exist_ok=True)  # Ensure the directory exists
        error_log_path = os.path.join(error_log_dir, "download_errors.txt")
        
        with open(error_log_path, "a") as error_log:
            error_log.write(f"URL: {url}\nError: {e}\n\n")
        
        return None

def download_fars_data(years, base_dir="data/raw"):
    """
    Downloads FARS data for the specified years in both CSV and SAS formats.
    For years 1978 and onwards, also downloads Puerto Rico data.
    For years 1982 and onwards, also downloads Auxiliary files.
    
    Args:
        years (list): List of years to download data for
        base_dir (str): Base directory to save downloaded files
    """
    base_url = "https://static.nhtsa.gov/nhtsa/downloads/FARS/"
    
    for year in years:
        year_str = str(year)
        
        # Create year-specific output directory
        year_dir = os.path.join(base_dir, year_str)
        
        # Base file types to download
        file_types = [""]  # Standard files (empty string means no suffix)
        
        # Add Auxiliary files for years 1982 and onwards
        if year >= 1982:
            file_types.append("Auxiliary")
        
        # File formats to download
        formats = [
            {"suffix": "CSV", "description": "CSV format"},
            {"suffix": "SAS", "description": "SAS format"}
        ]
        
        # Regions to download
        regions = ["National"]
        
        # Add Puerto Rico for years 1978 and onwards
        if year >= 1978:
            regions.append("Puerto Rico")
        
        print(f"\nProcessing year {year_str}...")
        
        for region in regions:
            region_url_part = region.replace(" ", "%20")  # URL encode spaces
            region_file_part = region.replace(" ", "")    # Remove spaces for filename
            
            for file_type in file_types:
                for format_info in formats:
                    # Special case for 1996 Auxiliary CSV file
                    if year == 1996 and file_type == "Auxiliary" and format_info["suffix"] == "CSV":
                        file_url = urljoin(base_url, f"{year_str}/{region_url_part}/FARS{year_str}{region_file_part}{file_type}CVS.zip")
                    else:
                        # Construct the URL for the file
                        file_url = urljoin(base_url, f"{year_str}/{region_url_part}/FARS{year_str}{region_file_part}{file_type}{format_info['suffix']}.zip")
                    
                    # Create description for logging
                    type_desc = f" {file_type}" if file_type else ""
                    
                    # Download the file
                    print(f"Attempting to download {region}{type_desc} {format_info['description']} for {year_str}...")
                    downloaded_file = download_file(file_url, year_dir)
                    
                    if downloaded_file:
                        print(f"FARS {region}{type_desc} {format_info['description']} for {year_str} downloaded successfully.")
                    else:
                        print(f"Failed to download FARS {region}{type_desc} {format_info['description']} for {year_str}.")
                    
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