#!/usr/bin/env python3
"""
Test Bible Clock using only fallback verses (offline mode).
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def main():
    load_dotenv()
    
    # Force offline mode
    os.environ['BIBLE_API_URL'] = ''
    os.environ['SIMULATION_MODE'] = 'true'
    
    from verse_manager import VerseManager
    from image_generator import ImageGenerator
    from display_manager import DisplayManager
    
    print("Testing Bible Clock with fallback verses...")
    
    try:
        verse_manager = VerseManager()
        image_generator = ImageGenerator()
        display_manager = DisplayManager()
        
        # Test getting a verse
        verse_data = verse_manager.get_current_verse()
        print(f"Retrieved verse: {verse_data['reference']}")
        print(f"Text: {verse_data['text'][:100]}...")
        
        # Test image generation
        image = image_generator.create_verse_image(verse_data)
        print(f"Generated image: {image.size}")
        
        # Test display (simulation)
        display_manager.display_image(image)
        print("✅ Fallback mode test successful!")
        
        # Save test image
        test_image_path = Path('test_fallback_output.png')
        image.save(test_image_path)
        print(f"Test image saved to: {test_image_path}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())