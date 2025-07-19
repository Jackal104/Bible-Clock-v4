#!/usr/bin/env python3
"""
Fix the contrast of e-paper optimized backgrounds and borders.
The current images are too light to be visible on e-ink displays.
"""

from PIL import Image, ImageEnhance
import os
from pathlib import Path

def enhance_image_contrast(input_path, output_path, contrast_factor=3.0, brightness_factor=0.7):
    """
    Enhance the contrast and reduce brightness of an image to make it more visible on e-ink.
    
    Args:
        input_path: Path to input image
        output_path: Path to save enhanced image
        contrast_factor: How much to increase contrast (higher = more contrast)
        brightness_factor: How much to adjust brightness (lower = darker)
    """
    try:
        # Open and convert to grayscale for e-ink optimization
        image = Image.open(input_path)
        if image.mode != 'L':
            image = image.convert('L')  # Convert to grayscale
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast_factor)
        
        # Adjust brightness (make darker)
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(brightness_factor)
        
        # Save the enhanced image
        image.save(output_path)
        print(f"Enhanced: {input_path} -> {output_path}")
        return True
        
    except Exception as e:
        print(f"Error enhancing {input_path}: {e}")
        return False

def fix_all_images():
    """Fix contrast for all new backgrounds and borders."""
    base_dir = Path("/home/admin/Bible-Clock-v4")
    
    # Fix backgrounds (indices 01-10)
    backgrounds_dir = base_dir / "images" / "backgrounds"
    print("Fixing background images...")
    for i in range(1, 11):
        filename = f"{i:02d}_*.png"
        files = list(backgrounds_dir.glob(filename))
        for file_path in files:
            # For backgrounds, use less aggressive enhancement since they should be subtle
            enhance_image_contrast(file_path, file_path, contrast_factor=2.0, brightness_factor=0.85)
    
    # Fix borders (indices 01-10) 
    borders_dir = base_dir / "images" / "borders"
    print("\nFixing border images...")
    for i in range(1, 11):
        filename = f"{i:02d}_*.png"
        files = list(borders_dir.glob(filename))
        for file_path in files:
            # For borders, use more aggressive enhancement since they need to be visible
            enhance_image_contrast(file_path, file_path, contrast_factor=4.0, brightness_factor=0.6)
    
    print("\nContrast enhancement complete!")

if __name__ == "__main__":
    fix_all_images()