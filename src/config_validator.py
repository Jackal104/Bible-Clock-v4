"""
Configuration validation and management.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

class ConfigValidator:
    """Validates and manages Bible Clock configuration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.errors = []
        self.warnings = []
    
    def validate_all(self) -> bool:
        """Run all validation checks."""
        self.errors.clear()
        self.warnings.clear()
        
        checks = [
            self._validate_environment,
            self._validate_data_files,
            self._validate_hardware_config,
            self._validate_api_config,
            self._validate_display_config
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.errors.append(f"Validation check failed: {e}")
        
        return len(self.errors) == 0
    
    def _validate_environment(self):
        """Validate environment variables."""
        required_vars = {
            'DISPLAY_WIDTH': int,
            'DISPLAY_HEIGHT': int,
            'BIBLE_API_URL': str
        }
        
        for var, expected_type in required_vars.items():
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Missing required environment variable: {var}")
            else:
                try:
                    if expected_type == int:
                        int(value)
                    elif expected_type == float:
                        float(value)
                except ValueError:
                    self.errors.append(f"Invalid type for {var}: expected {expected_type.__name__}")
    
    def _validate_data_files(self):
        """Validate required data files exist and are valid."""
        required_files = {
            'data/fallback_verses.json': self._validate_json,
            'data/bible_book_summaries_kjv_all_66.json': self._validate_json
        }
        
        for file_path, validator in required_files.items():
            path = Path(file_path)
            if not path.exists():
                self.errors.append(f"Missing required file: {file_path}")
            else:
                try:
                    validator(path)
                except Exception as e:
                    self.errors.append(f"Invalid file {file_path}: {e}")
    
    def _validate_json(self, file_path: Path):
        """Validate JSON file format."""
        with open(file_path, 'r') as f:
            json.load(f)  # Will raise JSONDecodeError if invalid
    
    def _validate_hardware_config(self):
        """Validate hardware configuration."""
        simulation_mode = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'
        
        if not simulation_mode:
            # Check for hardware libraries
            try:
                import RPi.GPIO
                import spidev
            except ImportError as e:
                self.warnings.append(f"Hardware library missing: {e}")
    
    def _validate_api_config(self):
        """Validate API configuration."""
        api_url = os.getenv('BIBLE_API_URL')
        if api_url:
            try:
                import requests
                response = requests.get(f"{api_url}/john%203:16", timeout=5)
                if response.status_code != 200:
                    self.warnings.append(f"Bible API not responding: HTTP {response.status_code}")
            except Exception as e:
                self.warnings.append(f"Cannot reach Bible API: {e}")
    
    def _validate_display_config(self):
        """Validate display configuration."""
        width = int(os.getenv('DISPLAY_WIDTH', '1872'))
        height = int(os.getenv('DISPLAY_HEIGHT', '1404'))
        
        if width <= 0 or height <= 0:
            self.errors.append("Display dimensions must be positive")
        
        if width * height > 10000000:  # ~10MP
            self.warnings.append("Very large display size may cause memory issues")
    
    def get_report(self) -> Dict[str, Any]:
        """Get validation report."""
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }