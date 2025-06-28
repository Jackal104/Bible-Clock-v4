#!/usr/bin/env python3
"""
Create premium, minimalist backgrounds optimized for text readability on e-ink displays.
Focus on clean, professional designs that enhance text visibility.
"""

from PIL import Image, ImageDraw, ImageFilter
import os
import math
from pathlib import Path

def create_background(width=1872, height=1404):
    """Create a background optimized for e-ink displays."""
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    return image, draw

def save_background(image, index, name, output_dir="images"):
    """Save background with proper naming convention."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = f"{index:02d}_{name.replace(' ', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    image.save(filepath)
    print(f"Created: {filepath}")

def create_premium_minimal_backgrounds():
    """Create premium minimalist backgrounds for optimal text readability."""
    backgrounds = []
    
    # 1. Pure White - The gold standard for text readability
    image, draw = create_background()
    backgrounds.append((image, "Pure_White"))
    
    # 2. Off White - Slightly warmer, easier on eyes
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FEFEFE')
    backgrounds.append((image, "Off_White"))
    
    # 3. Paper White - Mimics high-quality paper
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FFFEF7')
    backgrounds.append((image, "Paper_White"))
    
    # 4. Subtle Gray - Very light gray for reduced eye strain
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FAFAFA')
    backgrounds.append((image, "Subtle_Gray"))
    
    # 5. Elegant Border - Thin, professional border
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='white')
    draw.rectangle([0, 0, 1872, 3], fill='#E5E5E5')
    draw.rectangle([0, 1401, 1872, 1404], fill='#E5E5E5')
    draw.rectangle([0, 0, 3, 1404], fill='#E5E5E5')
    draw.rectangle([1869, 0, 1872, 1404], fill='#E5E5E5')
    backgrounds.append((image, "Elegant_Border"))
    
    # 6. Minimal Frame - Ultra-thin professional frame
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='white')
    draw.rectangle([50, 50, 1822, 52], fill='#F0F0F0')
    draw.rectangle([50, 1352, 1822, 1354], fill='#F0F0F0')
    draw.rectangle([50, 50, 52, 1354], fill='#F0F0F0')
    draw.rectangle([1820, 50, 1822, 1354], fill='#F0F0F0')
    backgrounds.append((image, "Minimal_Frame"))
    
    # 7. Clean Lines - Subtle divider lines for content sections
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='white')
    draw.rectangle([150, 200, 1722, 201], fill='#F5F5F5')
    draw.rectangle([150, 1200, 1722, 1201], fill='#F5F5F5')
    backgrounds.append((image, "Clean_Lines"))
    
    # 8. Soft Shadow - Very subtle drop shadow effect
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FCFCFC')
    draw.rectangle([100, 80, 1772, 1324], fill='white')
    draw.rectangle([102, 82, 1774, 1326], fill='#F8F8F8')
    draw.rectangle([100, 80, 1772, 1324], fill='white')
    backgrounds.append((image, "Soft_Shadow"))
    
    # 9. Modern Grid - Very subtle grid for organization
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='white')
    # Vertical guides
    for x in range(312, 1560, 312):
        for y in range(0, 1404, 20):
            draw.rectangle([x, y, x+1, y+10], fill='#FAFAFA')
    backgrounds.append((image, "Modern_Grid"))
    
    # 10. Center Focus - Subtle highlighting of center area
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FEFEFE')
    draw.rectangle([200, 150, 1672, 1254], fill='white')
    backgrounds.append((image, "Center_Focus"))
    
    # 11. Minimal Corners - Small corner accents
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='white')
    corner_size = 30
    # Very subtle corner markers
    draw.rectangle([0, 0, corner_size, 2], fill='#F0F0F0')
    draw.rectangle([0, 0, 2, corner_size], fill='#F0F0F0')
    draw.rectangle([1872-corner_size, 0, 1872, 2], fill='#F0F0F0')
    draw.rectangle([1870, 0, 1872, corner_size], fill='#F0F0F0')
    draw.rectangle([0, 1402, corner_size, 1404], fill='#F0F0F0')
    draw.rectangle([0, 1374, 2, 1404], fill='#F0F0F0')
    draw.rectangle([1872-corner_size, 1402, 1872, 1404], fill='#F0F0F0')
    draw.rectangle([1870, 1374, 1872, 1404], fill='#F0F0F0')
    backgrounds.append((image, "Minimal_Corners"))
    
    # 12. Text Zones - Areas optimized for different text sizes
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='white')
    # Header zone
    draw.rectangle([100, 100, 1772, 102], fill='#F8F8F8')
    # Main text zone (very subtle)
    draw.rectangle([150, 200, 1722, 1100], fill='#FEFEFE')
    # Footer zone
    draw.rectangle([100, 1300, 1772, 1302], fill='#F8F8F8')
    backgrounds.append((image, "Text_Zones"))
    
    # 13. Subtle Gradient - Very mild top-to-bottom fade
    image, draw = create_background()
    for y in range(1404):
        gray_value = 255 - int(y * 0.002)  # Very subtle gradient
        color = (gray_value, gray_value, gray_value)
        draw.line([(0, y), (1872, y)], fill=color)
    backgrounds.append((image, "Subtle_Gradient"))
    
    # 14. Reading Frame - Optimized for long-form text
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FDFDF8')
    draw.rectangle([250, 200, 1622, 1204], fill='white')
    draw.rectangle([248, 198, 1624, 1206], fill='#F5F5F5')
    draw.rectangle([250, 200, 1622, 1204], fill='white')
    backgrounds.append((image, "Reading_Frame"))
    
    # 15. Professional - Corporate-style clean background
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='white')
    draw.rectangle([0, 0, 1872, 60], fill='#FBFBFB')
    draw.rectangle([0, 1344, 1872, 1404], fill='#FBFBFB')
    backgrounds.append((image, "Professional"))
    
    # 16. Zen - Ultra-minimal for focus
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FEFEFE')
    # Single center dot for focus
    draw.ellipse([934, 700, 938, 704], fill='#F0F0F0')
    backgrounds.append((image, "Zen"))
    
    # 17. Classic Paper - Traditional book-like appearance
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FFFEF5')
    # Subtle paper texture using very light lines
    for i in range(0, 1404, 40):
        draw.line([(0, i), (1872, i)], fill='#FEFEF0', width=1)
    backgrounds.append((image, "Classic_Paper"))
    
    # 18. Modern Card - Card-like design with subtle elevation
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#F8F9FA')
    draw.rectangle([80, 60, 1792, 1344], fill='white')
    backgrounds.append((image, "Modern_Card"))
    
    # 19. Soft Margins - Gentle margin indicators
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='white')
    margin = 180
    # Soft margin indicators
    draw.rectangle([margin-1, 0, margin, 1404], fill='#FAFAFA')
    draw.rectangle([1872-margin, 0, 1872-margin+1, 1404], fill='#FAFAFA')
    draw.rectangle([0, margin-1, 1872, margin], fill='#FAFAFA')
    draw.rectangle([0, 1404-margin, 1872, 1404-margin+1], fill='#FAFAFA')
    backgrounds.append((image, "Soft_Margins"))
    
    # 20. Bright White - Maximum contrast for text
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FFFFFF')
    backgrounds.append((image, "Bright_White"))
    
    # 21. Warm White - Slightly warm tone
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FFFEF8')
    backgrounds.append((image, "Warm_White"))
    
    # 22. Cool White - Slightly cool tone
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FAFBFC')
    backgrounds.append((image, "Cool_White"))
    
    # 23. Notebook - Clean lined paper effect
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='white')
    # Very subtle horizontal lines
    for y in range(300, 1100, 50):
        draw.line([(200, y), (1672, y)], fill='#F5F5F5', width=1)
    # Left margin line
    draw.line([(250, 250), (250, 1150)], fill='#F0F0F0', width=2)
    backgrounds.append((image, "Notebook"))
    
    # 24. Minimal Shadow - Ultra-subtle depth
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FDFDFD')
    draw.rectangle([50, 40, 1822, 1364], fill='white')
    backgrounds.append((image, "Minimal_Shadow"))
    
    # 25. Clean Slate - Perfect neutral background
    image, draw = create_background()
    draw.rectangle([0, 0, 1872, 1404], fill='#FCFCFC')
    backgrounds.append((image, "Clean_Slate"))
    
    return backgrounds

def main():
    """Create all premium minimalist backgrounds."""
    print("Creating premium minimalist backgrounds for Bible Clock...")
    
    # Delete existing backgrounds
    images_dir = Path('images')
    thumbnails_dir = Path('src/web_interface/static/thumbnails')
    
    if images_dir.exists():
        for img_file in images_dir.glob('*.png'):
            img_file.unlink()
        print("Deleted existing backgrounds")
    
    if thumbnails_dir.exists():
        for thumb_file in thumbnails_dir.glob('thumb_*.jpg'):
            thumb_file.unlink()
        print("Deleted existing thumbnails")
    
    # Create new premium backgrounds
    all_backgrounds = create_premium_minimal_backgrounds()
    
    # Save all backgrounds
    for i, (image, name) in enumerate(all_backgrounds):
        save_background(image, i + 1, name)
    
    print(f"\nSuccessfully created {len(all_backgrounds)} premium minimalist backgrounds!")
    print("These backgrounds are specifically designed for:")
    print("- Maximum text readability on e-ink displays")
    print("- Professional, clean appearance")
    print("- Minimal eye strain during long reading sessions")
    print("- Perfect contrast for Bible verse display")
    print("- Zero distractions from the content")

if __name__ == "__main__":
    main()