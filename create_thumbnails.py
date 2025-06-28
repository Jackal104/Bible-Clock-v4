#!/usr/bin/env python3
"""
Generate web-optimized thumbnails for all background images.
"""

from PIL import Image
import os
from pathlib import Path

def create_thumbnails():
    """Generate thumbnails for all background images."""
    images_dir = Path('images')
    thumbnails_dir = Path('src/web_interface/static/thumbnails')
    
    # Create thumbnails directory if it doesn't exist
    thumbnails_dir.mkdir(parents=True, exist_ok=True)
    
    # Process all PNG files in images directory
    for image_file in sorted(images_dir.glob('*.png')):
        # Extract background number and name from filename
        filename_parts = image_file.stem.split('_', 1)
        if len(filename_parts) >= 2:
            bg_num = filename_parts[0]
            bg_name = filename_parts[1]
        else:
            bg_num = image_file.stem
            bg_name = "Background"
        
        # Load and resize image for thumbnail
        with Image.open(image_file) as img:
            # Create thumbnail (maintain aspect ratio, max 200x150)
            img.thumbnail((200, 150), Image.Resampling.LANCZOS)
            
            # Create new image with white background to ensure consistent size
            thumb = Image.new('RGB', (200, 150), 'white')
            
            # Calculate position to center the thumbnail
            x = (200 - img.width) // 2
            y = (150 - img.height) // 2
            
            # Paste the resized image onto the white background
            thumb.paste(img, (x, y))
            
            # Save as JPEG with high quality
            thumb_filename = f"thumb_{bg_num}_{bg_name}.jpg"
            thumb_path = thumbnails_dir / thumb_filename
            thumb.save(thumb_path, 'JPEG', quality=90, optimize=True)
            
            print(f"Created thumbnail: {thumb_path}")

if __name__ == "__main__":
    print("Generating thumbnails for premium backgrounds...")
    create_thumbnails()
    print("Thumbnail generation complete!")