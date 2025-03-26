import os
import ftplib
from datetime import datetime

def download_fars_data(output_dir):
    """
    Download FARS data from the NHTSA FTP site.
    
    :param output_dir: Directory to save downloaded files
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # FTP connection details
    ftp_server = 'ftp.nhtsa.dot.gov'
    ftp_path = '/FARS'
    
    try:
        # Establish FTP connection
        with ftplib.FTP(ftp_server) as ftp:
            print(f"Connecting to FTP server: {ftp_server}")
            ftp.login()
            ftp.set_pasv(True)  # Enable passive mode
            print("Login successful")
            print("Current directory:", ftp.pwd())
            ftp.cwd(ftp_path)
            print(f"Changed directory to: {ftp_path}")
            items = ftp.nlst()
            print("Available files and directories:", items)
            
            # Get current year for potential default download
            current_year = datetime.now().year
            
            # Download method (you can customize this)
            def download_file(filename):
                local_filepath = os.path.join(output_dir, filename)
                with open(local_filepath, 'wb') as local_file:
                    ftp.retrbinary(f'RETR {filename}', local_file.write)
                print(f"Downloaded: {filename}")
            
            # Example: Download all files (modify as needed)
            for item in items:
                try:
                    # Check if the item is a file
                    if ftp.size(item) is not None:  # If size is None, it's likely a directory
                        download_file(item)
                    else:
                        print(f"Skipping directory: {item}")
                except Exception as file_error:
                    print(f"Error processing {item}: {file_error}")
    
    except ftplib.all_errors as e:
        print(f"FTP error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Specify the output directory relative to the script's location
script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the script's directory
output_directory = os.path.join(script_dir, '..', 'data', 'raw')  # Move up one level to data/raw

# Run the download function
if __name__ == '__main__':
    download_fars_data(output_directory)
    print("FARS data download complete.")