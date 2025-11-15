"""
File and directory utility functions
"""

import os
import re
from pathlib import Path
from typing import Union


def ensure_directory(directory: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't

    Args:
        directory: Directory path

    Returns:
        Path object for the directory
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Union[str, Path], unit: str = 'KB') -> float:
    """
    Get file size

    Args:
        file_path: Path to file
        unit: Size unit - 'B', 'KB', 'MB', 'GB'

    Returns:
        File size in specified unit
    """
    size_bytes = Path(file_path).stat().st_size

    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024**2,
        'GB': 1024**3
    }

    if unit not in units:
        raise ValueError(f"Unknown unit: {unit}. Use: {list(units.keys())}")

    return size_bytes / units[unit]


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename by removing/replacing invalid characters

    Args:
        filename: Original filename
        max_length: Maximum filename length

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)

    # Replace spaces with underscores
    filename = filename.replace(' ', '_')

    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)

    # Trim to max length
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        name = name[:max_length - len(ext)]
        filename = name + ext

    return filename


def get_project_root() -> Path:
    """
    Get the project root directory

    Returns:
        Path to project root
    """
    # Assume this file is in src/utils/, so go up 2 levels
    return Path(__file__).parent.parent.parent


def get_data_directory(subdir: str = '') -> Path:
    """
    Get path to data directory

    Args:
        subdir: Subdirectory within data/ (e.g., 'streetview', 'sound')

    Returns:
        Path to data directory
    """
    data_dir = get_project_root() / 'data'

    if subdir:
        data_dir = data_dir / subdir

    return ensure_directory(data_dir)


def get_crash_directory(crash_id: str, data_type: str = '') -> Path:
    """
    Get directory for a specific crash

    Args:
        crash_id: Crash identifier
        data_type: Type of data ('streetview', 'sound', etc.)

    Returns:
        Path to crash directory
    """
    if data_type:
        base_dir = get_data_directory(data_type)
    else:
        base_dir = get_data_directory()

    crash_dir = base_dir / sanitize_filename(crash_id)
    return ensure_directory(crash_dir)


def list_files(directory: Union[str, Path], pattern: str = '*',
               recursive: bool = False) -> list:
    """
    List files in directory matching pattern

    Args:
        directory: Directory to search
        pattern: Glob pattern (e.g., '*.jpg', '**/*.csv')
        recursive: Search recursively

    Returns:
        List of Path objects
    """
    path = Path(directory)

    if recursive:
        if '**' not in pattern:
            pattern = f'**/{pattern}'
        return list(path.glob(pattern))
    else:
        return list(path.glob(pattern))


def count_files(directory: Union[str, Path], pattern: str = '*') -> int:
    """
    Count files in directory

    Args:
        directory: Directory to search
        pattern: Glob pattern

    Returns:
        Number of matching files
    """
    return len(list_files(directory, pattern))


# Example usage
if __name__ == '__main__':
    # Test directory creation
    test_dir = ensure_directory('test_output/subdir')
    print(f"Created directory: {test_dir}")

    # Test filename sanitization
    dirty_filename = 'test:file<name>/with*invalid?.txt'
    clean_filename = sanitize_filename(dirty_filename)
    print(f"Sanitized: {dirty_filename} -> {clean_filename}")

    # Test project paths
    print(f"Project root: {get_project_root()}")
    print(f"Data directory: {get_data_directory()}")
    print(f"Streetview directory: {get_data_directory('streetview')}")

    # Test crash directory
    crash_dir = get_crash_directory('AZ-2023-001', 'streetview')
    print(f"Crash directory: {crash_dir}")
