#!/usr/bin/env python3
"""Debug the verse drawing process step by step."""

import os
import sys
sys.path.append('/home/admin/Bible-Clock-v3')

from src.image_generator import ImageGenerator
from PIL import Image, ImageDraw
from pathlib import Path

def debug_verse_drawing():
    print("Debugging verse drawing process...")
    
    generator = ImageGenerator()
    
    # Create test verse data
    verse_data = {
        'reference': 'John 3:16',
        'text': 'For God so loved the world that he gave his one and only Son.',
        'book': 'John',
        'chapter': 3,
        'verse': 16
    }
    
    print(f"Verse data: {verse_data}")
    
    # Step 1: Test background loading
    print(f"\nBackgrounds available: {len(generator.backgrounds)}")
    if generator.backgrounds:
        background = generator.backgrounds[0].copy()
        background.save('debug_step1_background.png')
        print("✅ Background loaded and saved")
    else:
        print("❌ No backgrounds available")
        return
    
    # Step 2: Create overlay
    overlay = Image.new('RGBA', (generator.width, generator.height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    print("✅ Overlay created")
    
    # Step 3: Test font loading
    verse_text = verse_data['text']
    margin = 80
    content_width = generator.width - (2 * margin)
    
    optimal_font = generator._get_optimal_font_size(verse_text, content_width, margin)
    print(f"✅ Optimal font: {optimal_font}")
    print(f"Font size: {optimal_font.size if optimal_font else 'None'}")
    
    # Step 4: Test text wrapping
    wrapped_text = generator._wrap_text(verse_text, content_width, optimal_font)
    print(f"✅ Wrapped text: {wrapped_text}")
    
    # Step 5: Draw text manually
    if optimal_font and wrapped_text:
        y_position = margin + 100
        for i, line in enumerate(wrapped_text):
            line_bbox = draw.textbbox((0, 0), line, font=optimal_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (generator.width - line_width) // 2
            
            print(f"Drawing line {i}: '{line}' at ({line_x}, {y_position})")
            draw.text((line_x, y_position), line, fill=(0, 0, 0, 255), font=optimal_font)
            y_position += line_bbox[3] - line_bbox[1] + 20
        
        # Save overlay
        overlay.save('debug_step5_overlay.png')
        print("✅ Text drawn on overlay")
        
        # Step 6: Composite overlay onto background
        # Convert overlay to grayscale
        overlay_gray = overlay.convert('L')
        
        # Create mask from alpha channel
        alpha_channel = overlay.split()[-1]
        mask = alpha_channel.point(lambda x: 255 if x > 0 else 0)
        
        # Composite
        result = background.copy()
        result.paste(overlay_gray, mask=mask)
        
        result.save('debug_step6_final.png')
        print("✅ Final image composited and saved")
        
    else:
        print("❌ Font or wrapped text is None")

if __name__ == "__main__":
    debug_verse_drawing()