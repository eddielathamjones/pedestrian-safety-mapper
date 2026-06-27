import argparse
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
    os.makedirs(output_dir, exist_ok=True)

    filename = url.split('/')[-1]
    output_path = os.path.join(output_dir, filename)

    if os.path.exists(output_path):
        print(f"File {filename} already exists in {output_dir}, skipping download.")
        return output_path

    try:
        print(f"Downloading {filename} from {url}...")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"Successfully downloaded {filename} to {output_dir}")

        # Fix incorrect filename for 1996 Auxiliary CSV
        if "1996" in url and "AuxiliaryCVS.zip" in filename:
            corrected_filename = filename.replace("CVS", "CSV")
            corrected_output_path = os.path.join(output_dir, corrected_filename)
            os.rename(output_path, corrected_output_path)
            print(f"Renamed {filename} to {corrected_filename}")
            return corrected_output_path

        return output_path

    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")

        error_log_dir = os.path.join("data", "raw", "errors")
        os.makedirs(error_log_dir, exist_ok=True)
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
        year_dir = os.path.join(base_dir, year_str)

        file_types = [""]  # standard files
        if year >= 1982:
            file_types.append("Auxiliary")

        formats = [
            {"suffix": "CSV", "description": "CSV format"},
            {"suffix": "SAS", "description": "SAS format"},
        ]

        regions = ["National"]
        if year >= 1978:
            regions.append("Puerto Rico")

        print(f"\nProcessing year {year_str}...")

        for region in regions:
            region_url_part = region.replace(" ", "%20")
            region_file_part = region.replace(" ", "")

            for file_type in file_types:
                for format_info in formats:
                    if year == 1996 and file_type == "Auxiliary" and format_info["suffix"] == "CSV":
                        file_url = urljoin(
                            base_url,
                            f"{year_str}/{region_url_part}/FARS{year_str}{region_file_part}{file_type}CVS.zip",
                        )
                    else:
                        file_url = urljoin(
                            base_url,
                            f"{year_str}/{region_url_part}/FARS{year_str}{region_file_part}{file_type}{format_info['suffix']}.zip",
                        )

                    type_desc = f" {file_type}" if file_type else ""
                    print(f"Attempting to download {region}{type_desc} {format_info['description']} for {year_str}...")
                    downloaded_file = download_file(file_url, year_dir)

                    if downloaded_file:
                        print(f"FARS {region}{type_desc} {format_info['description']} for {year_str} downloaded successfully.")
                    else:
                        print(f"Failed to download FARS {region}{type_desc} {format_info['description']} for {year_str}.")

                    time.sleep(1)


def parse_years(years_str):
    """Parse '2025' or '2001-2025' into a list of ints."""
    if "-" in years_str:
        start, end = years_str.split("-", 1)
        return list(range(int(start), int(end) + 1))
    return [int(years_str)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download FARS NationalCSV zips from NHTSA.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python scripts/data_download.py --years 2025          # single new year\n"
               "  python scripts/data_download.py --years 2001-2025     # full range\n"
               "  python scripts/data_download.py                       # default: 1975-2024",
    )
    parser.add_argument(
        "--years",
        default="1975-2024",
        help="Year or inclusive range to download, e.g. '2025' or '2001-2025' (default: 1975-2024)",
    )
    parser.add_argument(
        "--data-dir",
        default=os.path.join("data", "raw"),
        help="Destination directory for downloaded zips (default: data/raw)",
    )
    args = parser.parse_args()

    years = parse_years(args.years)
    print(f"Downloading FARS data for {len(years)} year(s): {years[0]}–{years[-1]}")
    download_fars_data(years, args.data_dir)
    print("\nDownload process completed.")
