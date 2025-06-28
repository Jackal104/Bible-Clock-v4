#!/usr/bin/env python3
"""
Create additional background images with enhanced framing for the Bible Clock.
These will be more visually distinct and feature prominent framing elements.
"""

from PIL import Image, ImageDraw
import os

# E-ink display resolution (from display_manager.py)
WIDTH = 1872
HEIGHT = 1404

def create_thick_border_frame():
    """Create background with thick decorative border."""
    img = Image.new('L', (WIDTH, HEIGHT), 245)  # Light gray background
    draw = ImageDraw.Draw(img)
    
    # Thick outer border
    border_width = 40
    draw.rectangle([0, 0, WIDTH-1, HEIGHT-1], outline=100, width=border_width)
    
    # Inner decorative border
    inner_margin = border_width + 20
    draw.rectangle([inner_margin, inner_margin, WIDTH-inner_margin, HEIGHT-inner_margin], 
                   outline=150, width=8)
    
    # Corner decorations
    corner_size = 80
    for x in [inner_margin-20, WIDTH-inner_margin-corner_size+20]:
        for y in [inner_margin-20, HEIGHT-inner_margin-corner_size+20]:
            draw.rectangle([x, y, x+corner_size, y+corner_size], outline=120, width=4)
    
    return img

def create_ornate_corners():
    """Create background with ornate corner decorations."""
    img = Image.new('L', (WIDTH, HEIGHT), 250)
    draw = ImageDraw.Draw(img)
    
    # Main border
    draw.rectangle([30, 30, WIDTH-30, HEIGHT-30], outline=120, width=6)
    
    # Ornate corners
    corner_size = 120
    corner_positions = [(60, 60), (WIDTH-60-corner_size, 60), 
                       (60, HEIGHT-60-corner_size), (WIDTH-60-corner_size, HEIGHT-60-corner_size)]
    
    for x, y in corner_positions:
        # Draw ornate corner pattern
        draw.rectangle([x, y, x+corner_size, y+corner_size], outline=100, width=4)
        draw.rectangle([x+15, y+15, x+corner_size-15, y+corner_size-15], outline=140, width=2)
        draw.rectangle([x+30, y+30, x+corner_size-30, y+corner_size-30], outline=100, width=2)
        
        # Cross pattern in corner
        center_x, center_y = x + corner_size//2, y + corner_size//2
        draw.line([center_x-20, center_y, center_x+20, center_y], fill=120, width=3)
        draw.line([center_x, center_y-20, center_x, center_y+20], fill=120, width=3)
    
    return img

def create_gothic_arch():
    """Create background with gothic arch-style framing."""
    img = Image.new('L', (WIDTH, HEIGHT), 248)
    draw = ImageDraw.Draw(img)
    
    # Outer frame
    margin = 50
    draw.rectangle([margin, margin, WIDTH-margin, HEIGHT-margin], outline=110, width=8)
    
    # Gothic arch at top
    arch_height = 150
    arch_start_y = margin + 20
    arch_center_x = WIDTH // 2
    
    # Draw arch
    for i in range(5):
        offset = i * 15
        draw.arc([arch_center_x-200+offset, arch_start_y, arch_center_x+200-offset, arch_start_y+arch_height], 
                 0, 180, fill=120-i*10, width=4)
    
    # Side columns
    column_width = 20
    column_height = HEIGHT - 2*margin - 40
    for x in [margin+30, WIDTH-margin-30-column_width]:
        draw.rectangle([x, margin+arch_height//2, x+column_width, margin+column_height], 
                      outline=110, width=4)
        # Column details
        for detail_y in range(margin+arch_height//2+50, margin+column_height-50, 100):
            draw.rectangle([x-5, detail_y, x+column_width+5, detail_y+30], outline=130, width=2)
    
    return img

def create_art_deco_frame():
    """Create background with Art Deco style framing."""
    img = Image.new('L', (WIDTH, HEIGHT), 240)
    draw = ImageDraw.Draw(img)
    
    # Main frame
    margin = 40
    draw.rectangle([margin, margin, WIDTH-margin, HEIGHT-margin], outline=100, width=10)
    
    # Art Deco corner elements
    corner_size = 100
    for corner_x in [margin, WIDTH-margin-corner_size]:
        for corner_y in [margin, HEIGHT-margin-corner_size]:
            # Fan pattern
            center_x = corner_x + (corner_size if corner_x == margin else 0)
            center_y = corner_y + (corner_size if corner_y == margin else 0)
            
            for i in range(4):
                radius = 20 + i*15
                draw.arc([center_x-radius, center_y-radius, center_x+radius, center_y+radius],
                        0, 90, fill=120-i*10, width=3)
            
            # Geometric lines
            for i in range(3):
                offset = i * 20
                if corner_x == margin and corner_y == margin:  # Top-left
                    draw.line([corner_x+offset, corner_y+corner_size, corner_x+corner_size, corner_y+offset], 
                             fill=110, width=2)
                elif corner_x != margin and corner_y == margin:  # Top-right
                    draw.line([corner_x+corner_size-offset, corner_y+corner_size, corner_x, corner_y+offset], 
                             fill=110, width=2)
                elif corner_x == margin and corner_y != margin:  # Bottom-left
                    draw.line([corner_x+offset, corner_y, corner_x+corner_size, corner_y+corner_size-offset], 
                             fill=110, width=2)
                else:  # Bottom-right
                    draw.line([corner_x+corner_size-offset, corner_y, corner_x, corner_y+corner_size-offset], 
                             fill=110, width=2)
    
    return img

def create_double_border_classic():
    """Create background with double border classic design."""
    img = Image.new('L', (WIDTH, HEIGHT), 250)
    draw = ImageDraw.Draw(img)
    
    # Outer border
    outer_margin = 25
    draw.rectangle([outer_margin, outer_margin, WIDTH-outer_margin, HEIGHT-outer_margin], 
                   outline=90, width=12)
    
    # Inner border
    inner_margin = 80
    draw.rectangle([inner_margin, inner_margin, WIDTH-inner_margin, HEIGHT-inner_margin], 
                   outline=120, width=6)
    
    # Decorative elements between borders
    mid_margin = (outer_margin + inner_margin) // 2
    decoration_spacing = 150
    
    # Top and bottom decorations
    for x in range(decoration_spacing, WIDTH-decoration_spacing, decoration_spacing):
        for y in [mid_margin, HEIGHT-mid_margin]:
            draw.ellipse([x-15, y-8, x+15, y+8], outline=110, width=3)
    
    # Left and right decorations
    for y in range(decoration_spacing, HEIGHT-decoration_spacing, decoration_spacing):
        for x in [mid_margin, WIDTH-mid_margin]:
            draw.ellipse([x-8, y-15, x+8, y+15], outline=110, width=3)
    
    return img

def create_manuscript_border():
    """Create background inspired by medieval manuscript borders."""
    img = Image.new('L', (WIDTH, HEIGHT), 245)
    draw = ImageDraw.Draw(img)
    
    # Main border
    margin = 60
    draw.rectangle([margin, margin, WIDTH-margin, HEIGHT-margin], outline=100, width=8)
    
    # Inner decorative border
    inner_margin = margin + 30
    draw.rectangle([inner_margin, inner_margin, WIDTH-inner_margin, HEIGHT-inner_margin], 
                   outline=130, width=3)
    
    # Manuscript-style corner illuminations
    illum_size = 80
    for corner_x in [margin-20, WIDTH-margin-illum_size+20]:
        for corner_y in [margin-20, HEIGHT-margin-illum_size+20]:
            # Corner square
            draw.rectangle([corner_x, corner_y, corner_x+illum_size, corner_y+illum_size], 
                          outline=110, width=4)
            
            # Inner pattern
            draw.rectangle([corner_x+15, corner_y+15, corner_x+illum_size-15, corner_y+illum_size-15], 
                          outline=120, width=2)
            
            # Center ornament
            center_x, center_y = corner_x + illum_size//2, corner_y + illum_size//2
            draw.ellipse([center_x-12, center_y-12, center_x+12, center_y+12], outline=100, width=2)
            draw.ellipse([center_x-6, center_y-6, center_x+6, center_y+6], outline=140, width=2)
    
    # Side decorations
    decoration_size = 40
    for x in [margin + decoration_size, WIDTH - margin - decoration_size*2]:
        mid_y = HEIGHT // 2
        draw.ellipse([x, mid_y-decoration_size//2, x+decoration_size, mid_y+decoration_size//2], 
                    outline=115, width=3)
    
    return img

# Create the new background images
backgrounds = [
    ("26_Thick_Border", create_thick_border_frame),
    ("27_Ornate_Corners", create_ornate_corners),
    ("28_Gothic_Arch", create_gothic_arch),
    ("29_Art_Deco", create_art_deco_frame),
    ("30_Double_Border", create_double_border_classic),
    ("31_Manuscript", create_manuscript_border),
]

print("Creating enhanced framed background images...")

for name, create_func in backgrounds:
    img = create_func()
    filepath = f"images/{name}.png"
    img.save(filepath)
    print(f"Created: {filepath}")

print("\nAll enhanced background images created successfully!")
print("These new backgrounds feature more prominent framing elements:")
print("- Thick Border: Bold outer frame with decorative inner border")
print("- Ornate Corners: Elaborate corner decorations with cross patterns")
print("- Gothic Arch: Medieval cathedral-inspired arch framing")
print("- Art Deco: Geometric Art Deco style corner elements")
print("- Double Border: Classic double-border design with decorative elements")
print("- Manuscript: Medieval manuscript-inspired illuminated corners")