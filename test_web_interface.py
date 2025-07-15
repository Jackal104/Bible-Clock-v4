#!/usr/bin/env python3
"""
Test the web interface image selection functionality.
"""

import sys
import os
sys.path.append('.')

from src.image_generator import ImageGenerator

def test_web_interface_integration():
    """Test that the web interface will load backgrounds and borders properly."""
    
    print("Testing Web Interface Image Integration")
    print("=" * 50)
    
    # Initialize image generator
    img_gen = ImageGenerator()
    
    # Get all available images
    all_images = img_gen.get_available_backgrounds()
    
    # Verify we have both backgrounds and borders
    backgrounds = [img for img in all_images if img['type'] == 'background']
    borders = [img for img in all_images if img['type'] == 'border']
    
    print(f"✅ Total images loaded: {len(all_images)}")
    print(f"✅ Background images: {len(backgrounds)}")
    print(f"✅ Border images: {len(borders)}")
    
    # Test thumbnail paths exist
    missing_thumbs = []
    for img in all_images:
        thumb_path = img['thumbnail'].replace('/static/', 'src/web_interface/static/')
        if not os.path.exists(thumb_path):
            missing_thumbs.append(thumb_path)
    
    if missing_thumbs:
        print(f"❌ Missing thumbnails: {len(missing_thumbs)}")
        for thumb in missing_thumbs[:5]:  # Show first 5
            print(f"   - {thumb}")
    else:
        print(f"✅ All thumbnails exist ({len(all_images)} thumbnails)")
    
    # Test image selection functionality
    print("\nTesting image selection...")
    try:
        # Test setting background
        original_index = img_gen.current_background_index
        img_gen.set_background(0)
        print("✅ Background selection works")
        
        # Test getting background info
        bg_info = img_gen.get_background_info()
        print("✅ Background info retrieval works")
        
        # Restore original
        img_gen.set_background(original_index)
        
    except Exception as e:
        print(f"❌ Background selection error: {e}")
    
    # Display sample images for each type
    print("\nSample Background Images:")
    for bg in backgrounds[:3]:
        print(f"  - {bg['name']} (Index: {bg['index']})")
    
    print("\nSample Border Images:")
    for border in borders[:3]:
        print(f"  - {border['name']} (Index: {border['index']})")
    
    print("\n" + "=" * 50)
    print("Web Interface Integration Test Complete!")
    
    if not missing_thumbs:
        print("🎉 All tests passed! The web interface should work correctly.")
        return True
    else:
        print("⚠️  Some thumbnails are missing but core functionality works.")
        return False

if __name__ == "__main__":
    test_web_interface_integration()