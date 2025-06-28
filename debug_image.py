#!/usr/bin/env python3
"""Debug what image is being generated."""

import os
import sys
sys.path.append('/home/admin/Bible-Clock-v3')

from src.verse_manager import VerseManager
from src.image_generator import ImageGenerator

def main():
    print("Creating debug image...")
    
    # Initialize components
    verse_manager = VerseManager()
    image_generator = ImageGenerator()
    
    # Get current verse
    current_verse = verse_manager.get_current_verse()
    print(f"Current verse: {current_verse}")
    
    # Generate image
    image = image_generator.create_verse_image(current_verse)
    
    # Save for inspection
    image.save('debug_current_verse.png')
    print("Debug image saved as debug_current_verse.png")
    
    # Also test with a simple verse
    simple_verse = {
        'reference': 'John 3:16',
        'text': 'For God so loved the world that he gave his one and only Son.',
        'book': 'John',
        'chapter': 3,
        'verse': 16
    }
    
    simple_image = image_generator.create_verse_image(simple_verse)
    simple_image.save('debug_simple_verse.png')
    print("Simple verse image saved as debug_simple_verse.png")

if __name__ == "__main__":
    main()