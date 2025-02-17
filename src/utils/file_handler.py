"""File Handler Module

This module provides utilities for reading and writing JSON files and managing configurations.
"""

import json
from typing import Dict, Any, List, Union
import os

class FileHandler:
    """Handles file operations for the narrative writer."""
    
    @staticmethod
    def load_json(filepath: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Load and parse a JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            Parsed JSON content
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in {filepath}: {str(e)}", e.doc, e.pos)
    
    @staticmethod
    def save_json(filepath: str, data: Union[Dict[str, Any], List[Dict[str, Any]]], pretty: bool = True) -> None:
        """Save data to a JSON file.
        
        Args:
            filepath: Path where to save the file
            data: Data to save
            pretty: Whether to format JSON with indentation
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
        except IOError as e:
            raise IOError(f"Error writing to {filepath}: {str(e)}")
    
    @staticmethod
    def load_config(config_path: str = "config.json") -> Dict[str, Any]:
        """Load configuration from JSON file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        try:
            return FileHandler.load_json(config_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    @staticmethod
    def save_narrative(narrative: str, output_path: str) -> None:
        """Save generated narrative to a file.
        
        Args:
            narrative: Generated narrative text
            output_path: Path where to save the narrative
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            # Create directory if it doesn't exist and if path contains directories
            directory = os.path.dirname(output_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(narrative)
        except IOError as e:
            raise IOError(f"Error writing narrative to {output_path}: {str(e)}")
