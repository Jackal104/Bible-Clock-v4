#!/usr/bin/env python3
"""Test the flip transformations."""

import os
import sys
sys.path.append('/home/admin/Bible-Clock-v3')

from src.verse_manager import VerseManager
from src.image_generator import ImageGenerator

def main():
    print("Testing flip transformations...")
    
    # Initialize components
    verse_manager = VerseManager()
    image_generator = ImageGenerator()
    
    # Get current verse
    current_verse = verse_manager.get_current_verse()
    print(f"Current verse: {current_verse}")
    
    # Test with DISPLAY_MIRROR=false (no flipping)
    os.environ['DISPLAY_MIRROR'] = 'false'
    image_no_flip = image_generator.create_verse_image(current_verse)
    image_no_flip.save('debug_no_flip.png')
    print("No flip image saved")
    
    # Test with DISPLAY_MIRROR=true (both flips)
    os.environ['DISPLAY_MIRROR'] = 'true'
    image_both_flips = image_generator.create_verse_image(current_verse)
    image_both_flips.save('debug_both_flips.png')
    print("Both flips image saved")
    
    # Now force display the flipped version
    from src.display_manager import DisplayManager
    display_manager = DisplayManager()
    display_manager.display_image(image_both_flips, force_refresh=True)
    print("Flipped image displayed!")

if __name__ == "__main__":
    main()