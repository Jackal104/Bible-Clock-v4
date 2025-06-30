#!/usr/bin/env python3
"""
Background Change Script
Changes the background and triggers a full refresh only for the background change.
Regular verse updates will use smooth partial refreshes.
"""

import sys
import os
sys.path.append('src')

from image_generator import ImageGenerator
from verse_manager import VerseManager
from display_manager import DisplayManager

def main():
    try:
        # Initialize components
        ig = ImageGenerator()
        vm = VerseManager()
        dm = DisplayManager()
        
        print("Current Background Change Script")
        print("="*50)
        
        # Show current background info
        bg_info = ig.get_current_background_info()
        print(f"Current background: {bg_info['name']} ({bg_info['index'] + 1}/{bg_info['total']})")
        
        # Cycle to next background
        ig.cycle_background()
        
        # Get new background info
        new_bg_info = ig.get_current_background_info()
        print(f"New background: {new_bg_info['name']} ({new_bg_info['index'] + 1}/{new_bg_info['total']})")
        
        # Generate image with new background
        verse_data = vm.get_current_verse()
        print(f"Current verse: {verse_data.get('reference', 'Unknown')}")
        
        # This will trigger background change detection and force full refresh
        image = ig.create_verse_image(verse_data)
        
        # Check if background changed (should be True)
        background_changed = ig.background_changed_since_last_render()
        print(f"Background changed: {background_changed}")
        
        # Display with appropriate refresh mode
        dm.display_image(image, force_refresh=background_changed)
        
        if background_changed:
            print("✅ Full refresh applied for background change")
        else:
            print("✅ Partial refresh applied for verse update")
            
        print("\nBackground changed successfully!")
        print("Future verse updates will use smooth partial refreshes until next background change.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())