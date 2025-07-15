#!/usr/bin/env python3
"""
End-to-end test for Date Mode display - creates an actual image
"""

import sys
import os
sys.path.append('/home/mattk/projects/Bible-Clockv4')

def test_date_mode_end_to_end():
    print("Testing Date Mode end-to-end...")
    
    try:
        from src.verse_manager import VerseManager
        
        # Initialize verse manager in Date Mode
        vm = VerseManager()
        vm.display_mode = 'date'
        
        # Get verse data
        verse_data = vm.get_current_verse()
        print(f"✓ Verse data obtained")
        print(f"  - is_date_event: {verse_data.get('is_date_event', False)}")
        print(f"  - current_time: {verse_data.get('current_time', 'Not set')}")
        print(f"  - current_date: {verse_data.get('current_date', 'Not set')}")
        print(f"  - event_name: {verse_data.get('event_name', 'Not set')}")
        
        # Test the reference display text generation
        if verse_data.get('is_date_event'):
            from datetime import datetime
            now = datetime.now()
            current_time = verse_data.get('current_time', now.strftime('%I:%M %p'))
            current_date = verse_data.get('current_date', now.strftime('%B %d, %Y'))
            expected_reference_text = f"{current_time} - {current_date}"
            print(f"✓ Expected reference text: '{expected_reference_text}'")
        else:
            print("✗ is_date_event is False - this would cause the problem!")
        
        # Try to create an image (if PIL is available)
        try:
            from src.image_generator import ImageGenerator
            ig = ImageGenerator()
            
            print(f"✓ ImageGenerator initialized")
            print(f"  - Reference position: {ig.reference_position}")
            print(f"  - Reference Y offset: {ig.reference_y_offset}")
            print(f"  - Display mirror: {os.getenv('DISPLAY_MIRROR', 'false')}")
            
            # Create test image
            image = ig.create_verse_image(verse_data)
            print(f"✓ Image created successfully")
            
            # Save test image
            if image:
                image.save('/tmp/date_mode_test.png')
                print(f"✓ Test image saved to /tmp/date_mode_test.png")
                
                # Basic image analysis
                print(f"  - Image size: {image.size}")
                print(f"  - Image mode: {image.mode}")
            
        except ImportError as e:
            print(f"⚠ PIL not available, skipping image generation: {e}")
        except Exception as e:
            print(f"✗ Error creating image: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"✗ Error in end-to-end test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_date_mode_end_to_end()