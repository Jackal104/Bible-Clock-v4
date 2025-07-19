"""
Enhanced Image Generator with separate background and border support.
This allows pure white backgrounds with decorative borders and fixes artifacts.
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import logging

class EnhancedImageLayering:
    """Handles proper layering of backgrounds and borders."""
    
    def __init__(self, width=1872, height=1404):
        self.width = width
        self.height = height
        self.logger = logging.getLogger(__name__)
        
        # Separate indices for backgrounds and borders
        self.background_index = 0
        self.border_index = 0
        
        # Load available assets
        self._load_backgrounds()
        self._load_borders()
    
    def _load_backgrounds(self):
        """Load background images separately."""
        self.backgrounds = []
        self.background_names = []
        
        # Add pure white as first option
        self.backgrounds.append(None)  # None = pure white
        self.background_names.append("Pure White")
        
        # Load background files
        bg_dir = Path('images/backgrounds')
        if bg_dir.exists():
            for bg_file in sorted(bg_dir.glob('*.png')):
                try:
                    self.backgrounds.append(bg_file)
                    name = bg_file.stem
                    if '_' in name and name.split('_')[0].isdigit():
                        name = '_'.join(name.split('_')[1:]).replace('_', ' ')
                    self.background_names.append(name)
                    self.logger.debug(f"Loaded background: {name}")
                except Exception as e:
                    self.logger.warning(f"Failed to load background {bg_file}: {e}")
    
    def _load_borders(self):
        """Load border images separately."""
        self.borders = []
        self.border_names = []
        
        # Add "no border" as first option
        self.borders.append(None)  # None = no border
        self.border_names.append("No Border")
        
        # Load border files
        border_dir = Path('images/borders')
        if border_dir.exists():
            for border_file in sorted(border_dir.glob('*.png')):
                try:
                    self.borders.append(border_file)
                    name = border_file.stem
                    if '_' in name and name.split('_')[0].isdigit():
                        name = '_'.join(name.split('_')[1:]).replace('_', ' ')
                    self.border_names.append(name)
                    self.logger.debug(f"Loaded border: {name}")
                except Exception as e:
                    self.logger.warning(f"Failed to load border {border_file}: {e}")
    
    def create_layered_image(self) -> Image.Image:
        """Create a properly layered background + border image."""
        # Start with pure white base
        image = Image.new('L', (self.width, self.height), 255)
        
        # Layer 1: Background (if not pure white)
        if (self.background_index < len(self.backgrounds) and 
            self.backgrounds[self.background_index] is not None):
            
            bg_path = self.backgrounds[self.background_index]
            try:
                bg_img = Image.open(bg_path)
                bg_img = bg_img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                bg_img = bg_img.convert('L')  # Ensure grayscale
                image = bg_img.copy()
                self.logger.debug(f"Applied background: {bg_path.name}")
            except Exception as e:
                self.logger.warning(f"Failed to apply background {bg_path}: {e}")
        
        # Layer 2: Border (if selected)
        if (self.border_index < len(self.borders) and 
            self.borders[self.border_index] is not None):
            
            border_path = self.borders[self.border_index]
            try:
                border_img = Image.open(border_path)
                border_img = border_img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                border_img = border_img.convert('L')  # Ensure grayscale
                
                # Composite border over background
                # Use the border as a mask - only apply dark pixels from border
                import numpy as np
                
                image_array = np.array(image)
                border_array = np.array(border_img)
                
                # Apply border where it's darker than background
                # This preserves the background while adding border details
                mask = border_array < image_array
                image_array[mask] = border_array[mask]
                
                image = Image.fromarray(image_array, mode='L')
                self.logger.debug(f"Applied border: {border_path.name}")
                
            except Exception as e:
                self.logger.warning(f"Failed to apply border {border_path}: {e}")
        
        return image
    
    def set_background(self, index: int):
        """Set background by index."""
        if 0 <= index < len(self.backgrounds):
            self.background_index = index
            self.logger.info(f"Background set to: {self.background_names[index]}")
        else:
            self.logger.warning(f"Invalid background index: {index}")
    
    def set_border(self, index: int):
        """Set border by index."""
        if 0 <= index < len(self.borders):
            self.border_index = index
            self.logger.info(f"Border set to: {self.border_names[index]}")
        else:
            self.logger.warning(f"Invalid border index: {index}")
    
    def get_background_info(self) -> Dict:
        """Get current background information."""
        return {
            'index': self.background_index,
            'name': self.background_names[self.background_index] if self.background_index < len(self.background_names) else 'Unknown',
            'total': len(self.backgrounds)
        }
    
    def get_border_info(self) -> Dict:
        """Get current border information."""
        return {
            'index': self.border_index,
            'name': self.border_names[self.border_index] if self.border_index < len(self.border_names) else 'Unknown',
            'total': len(self.borders)
        }
    
    def get_available_backgrounds(self) -> List[Dict]:
        """Get list of available backgrounds."""
        return [
            {
                'index': i,
                'name': name,
                'current': i == self.background_index
            }
            for i, name in enumerate(self.background_names)
        ]
    
    def get_available_borders(self) -> List[Dict]:
        """Get list of available borders."""
        return [
            {
                'index': i,
                'name': name,
                'current': i == self.border_index
            }
            for i, name in enumerate(self.border_names)
        ]