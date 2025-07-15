#!/usr/bin/env python3

import sys
import os
sys.path.append('src')

from verse_manager import VerseManager

# Test the translation loading directly
def test_translations():
    vm = VerseManager()
    
    print("=== Verse Manager Translation Analysis ===")
    print(f"Available translations: {vm.get_available_translations()}")
    print(f"Display names: {vm.get_translation_display_names()}")
    
    print("\n=== Supported Translations Configuration ===")
    for key, value in vm.supported_translations.items():
        print(f"{key}: {value}")
    
    # Check if CEV file exists
    print("\n=== File System Check ===")
    cev_file = "data/translations/bible_cev.json"
    print(f"CEV file exists: {os.path.exists(cev_file)}")
    if os.path.exists(cev_file):
        stat = os.stat(cev_file)
        print(f"CEV file size: {stat.st_size} bytes")
    
    # Check all translation files
    import glob
    translation_files = glob.glob("data/translations/bible_*.json")
    print(f"Translation files found: {[os.path.basename(f) for f in translation_files]}")
    
if __name__ == "__main__":
    test_translations()