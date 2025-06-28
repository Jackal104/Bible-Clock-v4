#!/usr/bin/env python3
"""Clear display completely then show verse."""

import os
import sys
sys.path.append('/home/admin/Bible-Clock-v3')

from src.verse_manager import VerseManager
from src.image_generator import ImageGenerator
from src.display_manager import DisplayManager

def main():
    print("Clearing display completely...")
    
    # Initialize components
    verse_manager = VerseManager()
    image_generator = ImageGenerator()
    display_manager = DisplayManager()
    
    # First, clear display completely
    display_manager.clear_display()
    print("Display cleared!")
    
    # Wait a moment
    import time
    time.sleep(1)
    
    # Get current verse
    current_verse = verse_manager.get_current_verse()
    print(f"Current verse: {current_verse}")
    
    # Generate image
    image = image_generator.create_verse_image(current_verse)
    
    # Force display update with full refresh
    display_manager.display_image(image, force_refresh=True)
    print("Fresh verse displayed!")

if __name__ == "__main__":
    main()