#!/usr/bin/env python3
"""Debug font loading issues."""

import os
import sys
sys.path.append('/home/admin/Bible-Clock-v3')

from src.image_generator import ImageGenerator
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def test_font_loading():
    print("Testing font loading...")
    
    # Test system DejaVu fonts
    system_dejavu_path = Path('/usr/share/fonts/truetype/dejavu')
    if system_dejavu_path.exists():
        print(f"✅ System DejaVu path exists: {system_dejavu_path}")
        
        font_file = system_dejavu_path / 'DejaVuSans.ttf'
        if font_file.exists():
            print(f"✅ DejaVuSans.ttf exists: {font_file}")
            
            try:
                test_font = ImageFont.truetype(str(font_file), 48)
                print(f"✅ Successfully loaded font: {test_font}")
                
                # Test text rendering
                img = Image.new('L', (400, 200), 255)
                draw = ImageDraw.Draw(img)
                draw.text((20, 50), "Test Text", fill=0, font=test_font)
                img.save('debug_font_test.png')
                print("✅ Font test image saved as debug_font_test.png")
                
            except Exception as e:
                print(f"❌ Failed to load font: {e}")
        else:
            print(f"❌ DejaVuSans.ttf not found at {font_file}")
    else:
        print(f"❌ System DejaVu path not found: {system_dejavu_path}")
    
    # Test ImageGenerator font loading
    print("\nTesting ImageGenerator font loading...")
    generator = ImageGenerator()
    print(f"Title font: {generator.title_font}")
    print(f"Verse font: {generator.verse_font}")
    print(f"Reference font: {generator.reference_font}")
    
    # Test optimal font size function
    print("\nTesting optimal font size function...")
    test_text = "For God so loved the world that he gave his one and only Son."
    try:
        optimal_font = generator._get_optimal_font_size(test_text, 1600, 80)
        print(f"Optimal font: {optimal_font}")
        if optimal_font:
            print(f"Font size: {optimal_font.size}")
        else:
            print("❌ Optimal font is None!")
    except Exception as e:
        print(f"❌ Error in optimal font function: {e}")

if __name__ == "__main__":
    test_font_loading()