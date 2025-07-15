#!/usr/bin/env python3
"""
Create subtle, minimalist black-and-white/grayscale images for e-paper displays.
Optimized for 1872x1404 resolution with separate backgrounds and borders.
"""

from PIL import Image, ImageDraw, ImageFilter
import os
import math
import numpy as np
from pathlib import Path

def create_base_image(width=1872, height=1404):
    """Create a base image optimized for e-ink displays."""
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    return image, draw

def save_image(image, category, index, name):
    """Save image with proper directory structure."""
    output_dir = f"images/{category}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = f"{index:02d}_{name.replace(' ', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    image.save(filepath)
    print(f"Created: {filepath}")
    return filepath

def create_subtle_backgrounds():
    """Create subtle background patterns for Bible verse display."""
    backgrounds = []
    
    # 1. Pure White - Maximum readability
    image, draw = create_base_image()
    backgrounds.append((image, "Pure_White"))
    
    # 2. Subtle Dots Pattern
    image, draw = create_base_image()
    for x in range(0, 1872, 40):
        for y in range(0, 1404, 40):
            if (x + y) % 80 == 0:
                draw.ellipse([x-1, y-1, x+1, y+1], fill='#F8F8F8')
    backgrounds.append((image, "Subtle_Dots"))
    
    # 3. Light Grid Texture
    image, draw = create_base_image()
    for x in range(0, 1872, 60):
        draw.line([(x, 0), (x, 1404)], fill='#FAFAFA', width=1)
    for y in range(0, 1404, 60):
        draw.line([(0, y), (1872, y)], fill='#FAFAFA', width=1)
    backgrounds.append((image, "Light_Grid"))
    
    # 4. Diagonal Texture
    image, draw = create_base_image()
    for i in range(-1404, 1872, 80):
        draw.line([(i, 0), (i + 1404, 1404)], fill='#F9F9F9', width=1)
    backgrounds.append((image, "Diagonal_Lines"))
    
    # 5. Soft Gradient
    image, draw = create_base_image()
    for y in range(1404):
        gray_value = 255 - int(y * 0.01)
        gray_value = max(240, gray_value)  # Keep it very light
        color = (gray_value, gray_value, gray_value)
        draw.line([(0, y), (1872, y)], fill=color)
    backgrounds.append((image, "Soft_Gradient"))
    
    # 6. Paper Texture
    image, draw = create_base_image()
    draw.rectangle([0, 0, 1872, 1404], fill='#FFFEF8')
    # Add subtle paper grain
    for i in range(0, 1872, 3):
        for j in range(0, 1404, 3):
            if (i + j) % 15 == 0:
                draw.point((i, j), fill='#FEFEF5')
    backgrounds.append((image, "Paper_Texture"))
    
    # 7. Concentric Circles
    image, draw = create_base_image()
    center_x, center_y = 936, 702
    for radius in range(100, 800, 100):
        draw.ellipse([center_x-radius, center_y-radius, 
                     center_x+radius, center_y+radius], 
                     outline='#F8F8F8', width=1)
    backgrounds.append((image, "Concentric_Circles"))
    
    # 8. Hexagon Pattern
    image, draw = create_base_image()
    size = 30
    for x in range(0, 1872, size*2):
        for y in range(0, 1404, size*2):
            # Simple hexagon approximation with circles
            draw.ellipse([x-size//4, y-size//4, x+size//4, y+size//4], 
                        outline='#F9F9F9', width=1)
    backgrounds.append((image, "Hexagon_Pattern"))
    
    # 9. Cross Hatch
    image, draw = create_base_image()
    spacing = 40
    for i in range(0, 1872 + 1404, spacing):
        draw.line([(0, i), (i, 0)], fill='#FAFAFA', width=1)
        draw.line([(1872-i, 1404), (1872, 1404-i)], fill='#FAFAFA', width=1)
    backgrounds.append((image, "Cross_Hatch"))
    
    # 10. Minimalist Waves
    image, draw = create_base_image()
    for y in range(0, 1404, 80):
        points = []
        for x in range(0, 1872, 20):
            wave_y = y + int(5 * math.sin(x * 0.01))
            points.append((x, wave_y))
        if len(points) > 1:
            for i in range(len(points)-1):
                draw.line([points[i], points[i+1]], fill='#F8F8F8', width=1)
    backgrounds.append((image, "Minimalist_Waves"))
    
    return backgrounds

def create_elegant_borders():
    """Create elegant border designs for e-paper displays."""
    borders = []
    
    # 1. Classic Thin Border
    image, draw = create_base_image()
    draw.rectangle([10, 10, 1862, 1394], outline='#E0E0E0', width=3)
    borders.append((image, "Classic_Thin"))
    
    # 2. Double Line Border
    image, draw = create_base_image()
    draw.rectangle([20, 20, 1852, 1384], outline='#E0E0E0', width=2)
    draw.rectangle([30, 30, 1842, 1374], outline='#E0E0E0', width=1)
    borders.append((image, "Double_Line"))
    
    # 3. Corner Accents
    image, draw = create_base_image()
    corner_size = 80
    # Top-left
    draw.line([(20, 20), (20+corner_size, 20)], fill='#D0D0D0', width=3)
    draw.line([(20, 20), (20, 20+corner_size)], fill='#D0D0D0', width=3)
    # Top-right
    draw.line([(1852, 20), (1852-corner_size, 20)], fill='#D0D0D0', width=3)
    draw.line([(1852, 20), (1852, 20+corner_size)], fill='#D0D0D0', width=3)
    # Bottom-left
    draw.line([(20, 1384), (20+corner_size, 1384)], fill='#D0D0D0', width=3)
    draw.line([(20, 1384), (20, 1384-corner_size)], fill='#D0D0D0', width=3)
    # Bottom-right
    draw.line([(1852, 1384), (1852-corner_size, 1384)], fill='#D0D0D0', width=3)
    draw.line([(1852, 1384), (1852, 1384-corner_size)], fill='#D0D0D0', width=3)
    borders.append((image, "Corner_Accents"))
    
    # 4. Art Deco Style
    image, draw = create_base_image()
    # Main border
    draw.rectangle([15, 15, 1857, 1389], outline='#D0D0D0', width=2)
    # Corner decorations
    for corner_x, corner_y in [(15, 15), (1857, 15), (15, 1389), (1857, 1389)]:
        for i in range(3):
            offset = i * 5
            if corner_x < 100:  # Left corners
                x1, x2 = corner_x + offset, corner_x + 30 + offset
            else:  # Right corners
                x1, x2 = corner_x - offset, corner_x - 30 - offset
            if corner_y < 100:  # Top corners
                y1, y2 = corner_y + offset, corner_y + 30 + offset
            else:  # Bottom corners
                y1, y2 = corner_y - offset, corner_y - 30 - offset
            draw.line([(x1, corner_y), (x2, corner_y)], fill='#E5E5E5', width=1)
            draw.line([(corner_x, y1), (corner_x, y2)], fill='#E5E5E5', width=1)
    borders.append((image, "Art_Deco"))
    
    # 5. Geometric Pattern Border
    image, draw = create_base_image()
    # Main frame
    draw.rectangle([25, 25, 1847, 1379], outline='#D5D5D5', width=2)
    # Geometric pattern on border
    for x in range(25, 1847, 40):
        draw.rectangle([x, 25, x+20, 45], outline='#E8E8E8', width=1)
        draw.rectangle([x, 1359, x+20, 1379], outline='#E8E8E8', width=1)
    for y in range(25, 1379, 40):
        draw.rectangle([25, y, 45, y+20], outline='#E8E8E8', width=1)
        draw.rectangle([1827, y, 1847, y+20], outline='#E8E8E8', width=1)
    borders.append((image, "Geometric_Pattern"))
    
    # 6. Ornamental Frame
    image, draw = create_base_image()
    # Outer border
    draw.rectangle([10, 10, 1862, 1394], outline='#D0D0D0', width=4)
    # Inner decorative border
    draw.rectangle([20, 20, 1852, 1384], outline='#E5E5E5', width=1)
    # Ornamental corners
    corner_points = [(10, 10), (1862, 10), (10, 1394), (1862, 1394)]
    for x, y in corner_points:
        for i in range(5):
            size = 5 + i * 2
            if x < 100 and y < 100:  # Top-left
                draw.rectangle([x+i*3, y+i*3, x+size, y+size], outline='#E8E8E8', width=1)
            elif x > 100 and y < 100:  # Top-right
                draw.rectangle([x-size, y+i*3, x-i*3, y+size], outline='#E8E8E8', width=1)
            elif x < 100 and y > 100:  # Bottom-left
                draw.rectangle([x+i*3, y-size, x+size, y-i*3], outline='#E8E8E8', width=1)
            else:  # Bottom-right
                draw.rectangle([x-size, y-size, x-i*3, y-i*3], outline='#E8E8E8', width=1)
    borders.append((image, "Ornamental_Frame"))
    
    # 7. Minimalist Lines
    image, draw = create_base_image()
    # Simple elegant lines
    draw.line([(50, 50), (1822, 50)], fill='#E0E0E0', width=2)
    draw.line([(50, 1354), (1822, 1354)], fill='#E0E0E0', width=2)
    draw.line([(50, 50), (50, 1354)], fill='#E0E0E0', width=2)
    draw.line([(1822, 50), (1822, 1354)], fill='#E0E0E0', width=2)
    borders.append((image, "Minimalist_Lines"))
    
    # 8. Celtic Knot Inspired
    image, draw = create_base_image()
    draw.rectangle([30, 30, 1842, 1374], outline='#D0D0D0', width=3)
    # Corner knot patterns (simplified)
    corners = [(30, 30), (1842, 30), (30, 1374), (1842, 1374)]
    for x, y in corners:
        size = 40
        if x < 100 and y < 100:  # Top-left
            draw.arc([x, y, x+size, y+size], 0, 90, fill='#E0E0E0', width=2)
            draw.arc([x+10, y+10, x+size-10, y+size-10], 90, 180, fill='#E0E0E0', width=2)
        elif x > 100 and y < 100:  # Top-right
            draw.arc([x-size, y, x, y+size], 90, 180, fill='#E0E0E0', width=2)
            draw.arc([x-size+10, y+10, x-10, y+size-10], 180, 270, fill='#E0E0E0', width=2)
        elif x < 100 and y > 100:  # Bottom-left
            draw.arc([x, y-size, x+size, y], 270, 360, fill='#E0E0E0', width=2)
            draw.arc([x+10, y-size+10, x+size-10, y-10], 0, 90, fill='#E0E0E0', width=2)
        else:  # Bottom-right
            draw.arc([x-size, y-size, x, y], 180, 270, fill='#E0E0E0', width=2)
            draw.arc([x-size+10, y-size+10, x-10, y-10], 270, 360, fill='#E0E0E0', width=2)
    borders.append((image, "Celtic_Inspired"))
    
    # 9. Modern Gradient Border
    image, draw = create_base_image()
    border_width = 15
    for i in range(border_width):
        gray_value = 220 + int(i * 35 / border_width)
        color = (gray_value, gray_value, gray_value)
        draw.rectangle([i, i, 1872-i, 1404-i], outline=color, width=1)
    borders.append((image, "Modern_Gradient"))
    
    # 10. Dashed Border
    image, draw = create_base_image()
    dash_length = 20
    gap_length = 10
    # Top and bottom
    for x in range(20, 1852, dash_length + gap_length):
        draw.line([(x, 20), (x+dash_length, 20)], fill='#D0D0D0', width=3)
        draw.line([(x, 1384), (x+dash_length, 1384)], fill='#D0D0D0', width=3)
    # Left and right
    for y in range(20, 1384, dash_length + gap_length):
        draw.line([(20, y), (20, y+dash_length)], fill='#D0D0D0', width=3)
        draw.line([(1852, y), (1852, y+dash_length)], fill='#D0D0D0', width=3)
    borders.append((image, "Dashed_Border"))
    
    return borders

def main():
    """Generate all background and border images."""
    print("Creating e-paper optimized images (1872x1404)...")
    print("=" * 50)
    
    # Create backgrounds
    print("Creating subtle backgrounds...")
    backgrounds = create_subtle_backgrounds()
    created_files = []
    
    for i, (image, name) in enumerate(backgrounds):
        filepath = save_image(image, "backgrounds", i + 1, name)
        created_files.append(filepath)
    
    print(f"\nCreated {len(backgrounds)} background images")
    
    # Create borders
    print("\nCreating elegant borders...")
    borders = create_elegant_borders()
    
    for i, (image, name) in enumerate(borders):
        filepath = save_image(image, "borders", i + 1, name)
        created_files.append(filepath)
    
    print(f"\nCreated {len(borders)} border images")
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"✓ Created {len(backgrounds)} subtle background patterns")
    print(f"✓ Created {len(borders)} elegant border designs")
    print(f"✓ All images are 1872x1404 pixels (e-paper optimized)")
    print(f"✓ All images use grayscale/B&W palette suitable for e-ink")
    print(f"✓ Backgrounds are subtle enough for clear text overlay")
    print(f"✓ Borders are decorative but non-distracting")
    
    print("\nGenerated files:")
    for filepath in created_files:
        print(f"  {filepath}")
    
    print("\nDirect image URLs (for immediate use):")
    print("BACKGROUNDS:")
    for i in range(len(backgrounds)):
        print(f"  {i+1:02d}. /home/admin/Bible-Clock-v4/images/backgrounds/{i+1:02d}_{backgrounds[i][1].replace(' ', '_')}.png")
    
    print("\nBORDERS:")
    for i in range(len(borders)):
        print(f"  {i+1:02d}. /home/admin/Bible-Clock-v4/images/borders/{i+1:02d}_{borders[i][1].replace(' ', '_')}.png")

if __name__ == "__main__":
    main()