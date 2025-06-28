#!/usr/bin/env python3
"""Test display with proper mirroring through display manager."""

import os
import sys
sys.path.append('/home/admin/Bible-Clock-v3')

from src.verse_manager import VerseManager
from src.image_generator import ImageGenerator
from src.display_manager import DisplayManager

def main():
    print("Testing display with proper mirroring...")
    
    # Initialize components
    verse_manager = VerseManager()
    image_generator = ImageGenerator()
    display_manager = DisplayManager()
    
    # Get current verse
    current_verse = verse_manager.get_current_verse()
    print(f"Current verse: {current_verse}")
    
    # Generate image (this will have proper text now)
    image = image_generator.create_verse_image(current_verse)
    
    # Save the image before mirroring for comparison
    image.save('debug_before_mirror.png')
    print("Image saved as debug_before_mirror.png")
    
    # Now display through proper pipeline (this applies mirroring)
    display_manager.display_image(image, force_refresh=True)
    print("Image displayed with proper mirroring!")
    
    # Also save what would be sent to display after mirroring
    if os.getenv('DISPLAY_MIRROR', 'false').lower() == 'true':
        mirrored_image = image.transpose(image.FLIP_LEFT_RIGHT)
        mirrored_image.save('debug_after_mirror.png')
        print("Mirrored image saved as debug_after_mirror.png")

if __name__ == "__main__":
    main()