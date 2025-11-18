"""File loading utilities for different file formats."""
import json
import zipfile
import tarfile
import io
from typing import List, Tuple, Any


class FileLoader:
    """Handles loading JSON data from various file formats."""
    
    @staticmethod
    def load_json_file(file) -> Tuple[Any, str, str]:
        """
        Load a single JSON file.
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (json_data, file_name, error_message)
        """
        try:
            json_data = json.load(file)
            return json_data, file.name, None
        except json.JSONDecodeError as e:
            return None, file.name, f"Invalid JSON in file: {file.name}"
    
    @staticmethod
    def load_zip_archive(file) -> List[Tuple[Any, str, str]]:
        """
        Load JSON files from ZIP archive.
        
        Args:
            file: Uploaded ZIP file object
            
        Returns:
            List of tuples (json_data, file_name, error_message)
        """
        results = []
        
        try:
            archive_bytes = file.read()
            archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
            file_list = [f for f in archive.namelist() if f.endswith(".json") and "__MACOSX" not in f]
            
            for file_name in file_list:
                try:
                    with archive.open(file_name) as f:
                        json_data = json.load(io.TextIOWrapper(f, encoding='utf-8'))
                        results.append((json_data, file_name, None))
                except json.JSONDecodeError:
                    results.append((None, file_name, f"Invalid JSON in file: {file_name}"))
        
        except Exception as e:
            results.append((None, file.name, f"Error reading ZIP archive: {str(e)}"))
        
        return results
    
    @staticmethod
    def load_tar_archive(file) -> List[Tuple[Any, str, str]]:
        """
        Load JSON files from TAR archive.
        
        Args:
            file: Uploaded TAR file object
            
        Returns:
            List of tuples (json_data, file_name, error_message)
        """
        results = []
        
        try:
            archive_bytes = file.read()
            mode = "r:gz" if file.name.endswith((".tar.gz", ".gz")) else "r"
            
            with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode=mode) as archive:
                for member in archive.getmembers():
                    if member.name.endswith(".json") and "__MACOSX" not in member.name:
                        try:
                            f = archive.extractfile(member)
                            json_data = json.load(io.TextIOWrapper(f, encoding='utf-8'))
                            results.append((json_data, member.name, None))
                        except json.JSONDecodeError:
                            results.append((None, member.name, f"Invalid JSON in file: {member.name}"))
        
        except Exception as e:
            results.append((None, file.name, f"Error reading TAR archive: {str(e)}"))
        
        return results
    
    @staticmethod
    def categorize_files(uploaded_files) -> Tuple[List, List]:
        """
        Categorize uploaded files by type.
        
        Args:
            uploaded_files: List of uploaded file objects
            
        Returns:
            Tuple of (json_files, archive_files)
        """
        json_files = []
        archive_files = []
        
        for file in uploaded_files:
            if file.name.endswith('.json'):
                json_files.append(file)
            elif file.name.endswith(('.zip', '.tar', '.tar.gz', '.gz')):
                archive_files.append(file)
        
        return json_files, archive_files

