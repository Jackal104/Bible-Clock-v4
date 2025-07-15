#!/usr/bin/env python3
"""
Create thumbnails for both background and border images for web interface.
"""

from PIL import Image
import os
from pathlib import Path

def create_thumbnail(image_path, thumbnail_path, size=(150, 150)):
    """Create a thumbnail from an image."""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if needed (e.g., for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save as JPEG for web
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            print(f"Created thumbnail: {thumbnail_path}")
            return True
    except Exception as e:
        print(f"Error creating thumbnail for {image_path}: {e}")
        return False

def main():
    """Create thumbnails for all background and border images."""
    # Ensure thumbnail directory exists
    thumbnail_dir = Path('src/web_interface/static/thumbnails')
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    created_count = 0
    
    # Process background images
    backgrounds_dir = Path('images/backgrounds')
    if backgrounds_dir.exists():
        print("Creating thumbnails for background images...")
        for img_file in sorted(backgrounds_dir.glob('*.png')):
            # Extract number and name from filename (e.g., "01_Pure_White.png")
            base_name = img_file.stem  # e.g., "01_Pure_White"
            thumb_filename = f"bg_{base_name}_thumb.jpg"
            thumb_path = thumbnail_dir / thumb_filename
            
            if create_thumbnail(img_file, thumb_path):
                created_count += 1
    
    # Process border images  
    borders_dir = Path('images/borders')
    if borders_dir.exists():
        print("Creating thumbnails for border images...")
        for img_file in sorted(borders_dir.glob('*.png')):
            # Extract number and name from filename (e.g., "01_Classic_Thin.png")
            base_name = img_file.stem  # e.g., "01_Classic_Thin"
            thumb_filename = f"border_{base_name}_thumb.jpg"
            thumb_path = thumbnail_dir / thumb_filename
            
            if create_thumbnail(img_file, thumb_path):
                created_count += 1
    
    # Also create thumbnails for legacy images (moved to borders directory)
    legacy_borders = [
        "26_Thick_Border.png",
        "27_Ornate_Corners.png", 
        "28_Gothic_Arch.png",
        "29_Art_Deco.png",
        "30_Double_Border.png",
        "31_Manuscript.png"
    ]
    
    print("Creating thumbnails for legacy border images...")
    for legacy_file in legacy_borders:
        img_path = borders_dir / legacy_file
        if img_path.exists():
            base_name = img_path.stem
            thumb_filename = f"border_{base_name}_thumb.jpg"
            thumb_path = thumbnail_dir / thumb_filename
            
            if create_thumbnail(img_path, thumb_path):
                created_count += 1
    
    print(f"\nThumbnail creation complete!")
    print(f"Created {created_count} thumbnails in {thumbnail_dir}")
    
    # List all created thumbnails
    print("\nGenerated thumbnails:")
    for thumb in sorted(thumbnail_dir.glob('*_thumb.jpg')):
        print(f"  {thumb.name}")

if __name__ == "__main__":
    main()