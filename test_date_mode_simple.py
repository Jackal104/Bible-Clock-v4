#!/usr/bin/env python3
"""
Simple test for Date Mode reference display logic
"""

import sys
import os
sys.path.append('/home/mattk/projects/Bible-Clockv4')

from datetime import datetime

def test_reference_display_logic():
    print("Testing reference display logic for Date Mode...")
    
    # Simulate verse data for Date Mode
    verse_data = {
        'is_date_event': True,
        'current_time': '2:30 PM',
        'current_date': 'July 08, 2025',
        'event_name': 'King Saul Anointed'
    }
    
    # Test the logic from _add_verse_reference_display
    if verse_data.get('is_date_event'):
        now = datetime.now()
        current_time = verse_data.get('current_time', now.strftime('%I:%M %p'))
        current_date = verse_data.get('current_date', now.strftime('%B %d, %Y'))
        display_text = f"{current_time} - {current_date}"
        print(f"✓ Date Mode detected")
        print(f"✓ Display text should be: '{display_text}'")
    else:
        print("✗ Date Mode not detected - this is the issue!")
    
    # Check environment variables
    mirror_setting = os.getenv('DISPLAY_MIRROR', 'false').lower()
    print(f"✓ DISPLAY_MIRROR setting: {mirror_setting}")
    
    # Test with actual verse manager
    try:
        from src.verse_manager import VerseManager
        vm = VerseManager()
        vm.display_mode = 'date'
        actual_verse_data = vm.get_current_verse()
        
        print(f"✓ Actual verse data has is_date_event: {actual_verse_data.get('is_date_event', False)}")
        print(f"✓ Actual current_time: {actual_verse_data.get('current_time', 'Not set')}")
        print(f"✓ Actual current_date: {actual_verse_data.get('current_date', 'Not set')}")
        
        if actual_verse_data.get('is_date_event'):
            actual_display_text = f"{actual_verse_data.get('current_time')} - {actual_verse_data.get('current_date')}"
            print(f"✓ Actual display text should be: '{actual_display_text}'")
        else:
            print("✗ Actual verse data is missing is_date_event flag!")
            
    except Exception as e:
        print(f"✗ Error testing verse manager: {e}")

if __name__ == "__main__":
    test_reference_display_logic()