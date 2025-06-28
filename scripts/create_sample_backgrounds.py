#!/usr/bin/env python3
"""
Create sample background images for Bible Clock.
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_sample_backgrounds():
    """Create sample background images."""
    images_dir = Path('images')
    images_dir.mkdir(exist_ok=True)
    
    width, height = 1872, 1404
    
    backgrounds = [
        ('subtle_cross.png', create_subtle_cross),
        ('minimalist_frame.png', create_minimalist_frame),
        ('parchment.png', create_parchment),
        ('stained_glass.png', create_stained_glass),
        ('nature_border.png', create_nature_border),
        ('geometric.png', create_geometric),
        ('watercolor.png', create_watercolor),
        ('classic_scroll.png', create_classic_scroll)
    ]
    
    for filename, create_func in backgrounds:
        filepath = images_dir / filename
        if not filepath.exists():
            print(f"Creating {filename}...")
            img = create_func(width, height)
            img.save(filepath)
            print(f"Saved {filename}")
        else:
            print(f"{filename} already exists, skipping")

def create_subtle_cross(width, height):
    """Create a subtle cross background."""
    img = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(img)
    
    # Draw subtle cross lines
    center_x, center_y = width // 2, height // 2
    cross_width = 20
    
    # Vertical line
    draw.rectangle([center_x - cross_width//2, 0, center_x + cross_width//2, height], fill=245)
    
    # Horizontal line
    draw.rectangle([0, center_y - cross_width//2, width, center_y + cross_width//2], fill=245)
    
    # Add border
    draw.rectangle([0, 0, width-1, height-1], outline=200, width=5)
    
    return img

def create_minimalist_frame(width, height):
    """Create a minimalist frame background."""
    img = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(img)
    
    # Multiple nested frames
    margins = [20, 40, 60]
    grays = [180, 200, 220]
    
    for margin, gray in zip(margins, grays):
        draw.rectangle([margin, margin, width-margin-1, height-margin-1], outline=gray, width=2)
    
    return img

def create_parchment(width, height):
    """Create a parchment-style background."""
    img = Image.new('L', (width, height), 250)
    draw = ImageDraw.Draw(img)
    
    # Add texture with random dots
    import random
    for _ in range(1000):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        gray = random.randint(240, 255)
        draw.point((x, y), fill=gray)
    
    # Add aged corners
    corner_size = 100
    for corner in [(0, 0), (width-corner_size, 0), (0, height-corner_size), (width-corner_size, height-corner_size)]:
        draw.ellipse([corner[0], corner[1], corner[0]+corner_size, corner[1]+corner_size], fill=235)
    
    return img

def create_stained_glass(width, height):
    """Create a stained glass pattern background."""
    img = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(img)
    
    # Create geometric patterns
    step = 100
    for x in range(0, width, step):
        for y in range(0, height, step):
            gray = 220 + (x + y) % 35
            draw.rectangle([x, y, x+step-1, y+step-1], fill=gray, outline=180, width=2)
    
    return img

def create_nature_border(width, height):
    """Create a nature-inspired border."""
    img = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(img)
    
    # Create leaf-like border
    border_width = 80
    
    # Top and bottom borders
    for i in range(0, width, 20):
        draw.ellipse([i, 0, i+15, border_width], fill=230)
        draw.ellipse([i, height-border_width, i+15, height], fill=230)
    
    # Left and right borders
    for i in range(0, height, 20):
        draw.ellipse([0, i, border_width, i+15], fill=230)
        draw.ellipse([width-border_width, i, width, i+15], fill=230)
    
    return img

def create_geometric(width, height):
    """Create a geometric pattern background."""
    img = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(img)
    
    # Create diamond pattern
    size = 60
    for x in range(0, width, size):
        for y in range(0, height, size):
            points = [
                (x + size//2, y),
                (x + size, y + size//2),
                (x + size//2, y + size),
                (x, y + size//2)
            ]
            gray = 240 if (x//size + y//size) % 2 == 0 else 250
            draw.polygon(points, fill=gray, outline=220)
    
    return img

def create_watercolor(width, height):
    """Create a watercolor-style background."""
    img = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(img)
    
    # Create soft circular patterns
    import random
    for _ in range(50):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(100, 300)
        gray = random.randint(240, 255)
        draw.ellipse([x-size//2, y-size//2, x+size//2, y+size//2], fill=gray)
    
    return img

def create_classic_scroll(width, height):
    """Create a classic scroll background."""
    img = Image.new('L', (width, height), 250)
    draw = ImageDraw.Draw(img)
    
    # Add scroll borders
    border_height = 60
    
    # Top scroll
    draw.rectangle([0, 0, width, border_height], fill=230)
    draw.rectangle([0, border_height-10, width, border_height], fill=210)
    
    # Bottom scroll
    draw.rectangle([0, height-border_height, width, height], fill=230)
    draw.rectangle([0, height-border_height, width, height-border_height+10], fill=210)
    
    # Side decorations
    for y in range(border_height, height-border_height, 40):
        draw.rectangle([0, y, 20, y+20], fill=240)
        draw.rectangle([width-20, y, width, y+20], fill=240)
    
    return img

if __name__ == '__main__':
    create_sample_backgrounds()
    print("Sample backgrounds created successfully!")