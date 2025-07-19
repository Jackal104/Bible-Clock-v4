#!/usr/bin/env python3
"""
Create additional background and border patterns with better contrast for e-ink displays.
"""

from PIL import Image, ImageDraw, ImageFilter
import os
import math
import numpy as np
from pathlib import Path

def create_base_image(width=1872, height=1404):
    """Create a base image for e-ink displays."""
    image = Image.new('L', (width, height), 255)  # Start with white
    draw = ImageDraw.Draw(image)
    return image, draw

def save_image(image, category, index, name):
    """Save image with proper naming."""
    output_dir = f"images/{category}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = f"{index:02d}_{name.replace(' ', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    image.save(filepath)
    print(f"Created: {filepath}")
    return filepath

def create_additional_backgrounds():
    """Create more background patterns with good e-ink contrast."""
    backgrounds = []
    
    # Start index from 11 to avoid conflicts
    start_index = 11
    
    # 11. Linen Texture
    image, draw = create_base_image()
    for i in range(0, 1872, 2):
        for j in range(0, 1404, 2):
            if (i + j) % 8 == 0:
                draw.point((i, j), fill=240)
    backgrounds.append((image, "Linen_Texture"))
    
    # 12. Subtle Watermark
    image, draw = create_base_image()
    center_x, center_y = 936, 702
    for radius in range(200, 600, 50):
        draw.ellipse([center_x-radius, center_y-radius, 
                     center_x+radius, center_y+radius], 
                     outline=245, width=1)
    backgrounds.append((image, "Subtle_Watermark"))
    
    # 13. Parchment
    image, draw = create_base_image()
    # Create aged parchment effect
    for y in range(1404):
        for x in range(1872):
            if (x * y) % 1000 == 0:
                draw.point((x, y), fill=235)
    # Add some horizontal lines like old paper
    for y in range(100, 1404, 150):
        draw.line([(0, y), (1872, y)], fill=240, width=1)
    backgrounds.append((image, "Parchment"))
    
    # 14. Diamond Pattern
    image, draw = create_base_image()
    for x in range(0, 1872, 60):
        for y in range(0, 1404, 60):
            # Create diamond shapes
            diamond_size = 20
            points = [
                (x, y - diamond_size),
                (x + diamond_size, y),
                (x, y + diamond_size),
                (x - diamond_size, y)
            ]
            draw.polygon(points, outline=230, width=1)
    backgrounds.append((image, "Diamond_Pattern"))
    
    # 15. Fabric Weave
    image, draw = create_base_image()
    for x in range(0, 1872, 10):
        draw.line([(x, 0), (x, 1404)], fill=240, width=1)
    for y in range(0, 1404, 10):
        draw.line([(0, y), (1872, y)], fill=240, width=1)
    # Add weave pattern
    for x in range(0, 1872, 20):
        for y in range(0, 1404, 20):
            if (x // 20 + y // 20) % 2 == 0:
                draw.rectangle([x, y, x+10, y+10], fill=245)
    backgrounds.append((image, "Fabric_Weave"))
    
    return backgrounds, start_index

def create_additional_borders():
    """Create more border patterns with good e-ink contrast."""
    borders = []
    
    # Start index from 11 to avoid conflicts
    start_index = 11
    
    # 11. Victorian Border
    image, draw = create_base_image()
    # Main border
    draw.rectangle([30, 30, 1842, 1374], outline=120, width=4)
    # Decorative corners
    corner_size = 80
    corners = [(30, 30), (1842, 30), (30, 1374), (1842, 1374)]
    for x, y in corners:
        # Create ornate corner patterns
        for i in range(5):
            offset = i * 8
            if x < 100:  # Left side
                draw.line([(x + offset, y), (x + offset, y + corner_size)], fill=150, width=2)
            else:  # Right side
                draw.line([(x - offset, y), (x - offset, y + corner_size)], fill=150, width=2)
    borders.append((image, "Victorian_Border"))
    
    # 12. Chain Link Border
    image, draw = create_base_image()
    # Create chain-like border
    chain_spacing = 40
    for x in range(20, 1852, chain_spacing):
        # Top border
        draw.ellipse([x, 20, x+30, 40], outline=140, width=3)
        # Bottom border
        draw.ellipse([x, 1364, x+30, 1384], outline=140, width=3)
    for y in range(20, 1384, chain_spacing):
        # Left border
        draw.ellipse([20, y, 40, y+30], outline=140, width=3)
        # Right border
        draw.ellipse([1832, y, 1852, y+30], outline=140, width=3)
    borders.append((image, "Chain_Link_Border"))
    
    # 13. Braided Border
    image, draw = create_base_image()
    # Create braided pattern
    braid_width = 15
    # Top and bottom
    for x in range(0, 1872, 30):
        draw.ellipse([x, 10, x+20, 30], outline=130, width=2)
        draw.ellipse([x+10, 20, x+30, 40], outline=130, width=2)
        draw.ellipse([x, 1364, x+20, 1384], outline=130, width=2)
        draw.ellipse([x+10, 1374, x+30, 1394], outline=130, width=2)
    # Left and right
    for y in range(0, 1404, 30):
        draw.ellipse([10, y, 30, y+20], outline=130, width=2)
        draw.ellipse([20, y+10, 40, y+30], outline=130, width=2)
        draw.ellipse([1832, y, 1852, y+20], outline=130, width=2)
        draw.ellipse([1842, y+10, 1862, y+30], outline=130, width=2)
    borders.append((image, "Braided_Border"))
    
    # 14. Gothic Arch Border
    image, draw = create_base_image()
    # Main border
    draw.rectangle([40, 40, 1832, 1364], outline=110, width=5)
    # Gothic arch details at corners
    arch_height = 60
    for corner_x, corner_y in [(40, 40), (1832, 40), (40, 1364), (1832, 1364)]:
        # Create pointed arch effect
        if corner_y < 100:  # Top corners
            points = [(corner_x-20, corner_y), (corner_x, corner_y-20), (corner_x+20, corner_y)]
            draw.polygon(points, outline=110, width=2)
        else:  # Bottom corners
            points = [(corner_x-20, corner_y), (corner_x, corner_y+20), (corner_x+20, corner_y)]
            draw.polygon(points, outline=110, width=2)
    borders.append((image, "Gothic_Arch_Border"))
    
    # 15. Rope Border
    image, draw = create_base_image()
    # Create rope-like twisted border
    rope_thickness = 12
    # Draw main border frame
    draw.rectangle([25, 25, 1847, 1379], outline=100, width=rope_thickness)
    # Add rope texture with twisted lines
    for offset in range(0, rope_thickness, 3):
        # Top and bottom
        for x in range(25, 1847, 15):
            y_top = 25 + offset + int(3 * math.sin(x * 0.05))
            y_bottom = 1379 - offset + int(3 * math.sin(x * 0.05))
            draw.line([(x, y_top), (x+10, y_top)], fill=120, width=1)
            draw.line([(x, y_bottom), (x+10, y_bottom)], fill=120, width=1)
        # Left and right
        for y in range(25, 1379, 15):
            x_left = 25 + offset + int(3 * math.sin(y * 0.05))
            x_right = 1847 - offset + int(3 * math.sin(y * 0.05))
            draw.line([(x_left, y), (x_left, y+10)], fill=120, width=1)
            draw.line([(x_right, y), (x_right, y+10)], fill=120, width=1)
    borders.append((image, "Rope_Border"))
    
    return borders, start_index

def main():
    """Generate additional background and border images."""
    print("Creating additional e-ink optimized images...")
    print("=" * 50)
    
    # Create additional backgrounds
    print("\\nGenerating additional backgrounds...")
    backgrounds, bg_start = create_additional_backgrounds()
    for i, (image, name) in enumerate(backgrounds):
        save_image(image, "backgrounds", bg_start + i, name)
    
    # Create additional borders
    print("\\nGenerating additional borders...")
    borders, border_start = create_additional_borders()
    for i, (image, name) in enumerate(borders):
        save_image(image, "borders", border_start + i, name)
    
    print(f"\\nCreated {len(backgrounds)} additional backgrounds and {len(borders)} additional borders!")
    print("All images are optimized for e-ink displays with proper contrast.")

if __name__ == "__main__":
    main()