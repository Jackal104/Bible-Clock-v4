#!/usr/bin/env python3
"""
Aggressive ghosting removal script for Bible Clock e-ink display.
Run this if you notice faint text from previous displays.
"""

import sys
import os
sys.path.append('/home/admin/Bible-Clock-v3/src')

from display_manager import DisplayManager

def main():
    print("🧹 Starting aggressive ghosting removal...")
    print("This will perform multiple black/white refresh cycles to eliminate ghost text.")
    
    try:
        # Initialize display manager
        display_manager = DisplayManager()
        
        # Perform aggressive ghosting removal
        display_manager.clear_ghosting()
        
        print("✅ Ghosting removal completed!")
        print("The display should now be clear of any faint text.")
        
    except Exception as e:
        print(f"❌ Error during ghosting removal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()