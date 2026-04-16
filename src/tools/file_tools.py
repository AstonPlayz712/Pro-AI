"""File manipulation tools"""

import os
from typing import List, Optional


class FileTools:
    """Tools for file operations"""

    def __init__(self, base_directory: str = "."):
        """
        Initialize file tools.

        Args:
            base_directory: Base directory for file operations (for security)
        """
        self.base_directory = base_directory

    def read_file(self, file_path: str) -> str:
        """
        Read and return file contents.

        Args:
            file_path: Path to the file

        Returns:
            File contents as string
        """
        # TODO: Add security checks to prevent directory traversal
        try:
            with open(file_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return f"File not found: {file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, file_path: str, content: str) -> bool:
        """
        Write content to a file.

        Args:
            file_path: Path to the file
            content: Content to write

        Returns:
            True if successful, False otherwise
        """
        # TODO: Add security checks to prevent directory traversal
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing file: {str(e)}")
            return False

    def list_files(self, directory: str = ".") -> List[str]:
        """
        List files in a directory.

        Args:
            directory: Directory path

        Returns:
            List of file names
        """
        # TODO: Add security checks to prevent directory traversal
        try:
            return os.listdir(directory)
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return []

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists"""
        return os.path.exists(file_path)

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file.

        Args:
            file_path: Path to the file

        Returns:
            True if successful, False otherwise
        """
        # TODO: Add security checks
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
