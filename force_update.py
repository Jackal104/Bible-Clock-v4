#!/usr/bin/env python3
"""Force a display update to clear any lingering overlays."""

import os
import sys
sys.path.append('/home/admin/Bible-Clock-v3')

from src.verse_manager import VerseManager
from src.image_generator import ImageGenerator
from src.display_manager import DisplayManager

def main():
    print("Forcing display update...")
    
    # Initialize components
    verse_manager = VerseManager()
    image_generator = ImageGenerator()
    display_manager = DisplayManager()
    
    # Get current verse
    current_verse = verse_manager.get_current_verse()
    print(f"Current verse: {current_verse}")
    
    # Generate image
    image = image_generator.create_verse_image(current_verse)
    
    # Force display update
    display_manager.display_image(image, force_refresh=True)
    print("Display updated!")

if __name__ == "__main__":
    main()