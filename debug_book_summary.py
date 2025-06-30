#!/usr/bin/env python3
"""
Debug script to test book summary behavior at 11:00 (minute 00)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime
import json
from verse_manager import VerseManager

def test_book_summary_at_11_00():
    """Test what happens at 11:00 (minute 00)"""
    
    print("=== Testing Book Summary Behavior at 11:00 ===")
    
    # Create verse manager
    vm = VerseManager()
    vm.display_mode = 'time'  # Use time-based mode
    
    print(f"Display mode: {vm.display_mode}")
    print(f"Time format: {vm.time_format}")
    
    # Mock the current time to 11:00
    import unittest.mock
    mock_time = datetime(2025, 6, 30, 11, 0, 0)  # 11:00 AM
    
    with unittest.mock.patch('verse_manager.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_time
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        print(f"Mocked time: {mock_time.strftime('%H:%M')}")
        
        # Get the verse data
        verse_data = vm._get_time_based_verse()
        
        print("\n=== Verse Data ===")
        for key, value in verse_data.items():
            print(f"{key}: {value}")
        
        print("\n=== Analysis ===")
        print(f"Is summary: {verse_data.get('is_summary', False)}")
        print(f"Is time-based summary: {verse_data.get('is_time_based_summary', False)}")
        print(f"Book: {verse_data.get('book', 'N/A')}")
        print(f"Chapter: {verse_data.get('chapter', 'N/A')}")
        print(f"Verse: {verse_data.get('verse', 'N/A')}")
        print(f"Reference: {verse_data.get('reference', 'N/A')}")
        
        # Test what reference text would be displayed
        print("\n=== Testing Reference Display Logic ===")
        if verse_data.get('is_date_event'):
            display_text = mock_time.strftime('%B %d, %Y')
        else:
            display_text = verse_data.get('reference', 'Unknown')
        
        print(f"Reference text that would be displayed: '{display_text}'")

def test_minute_zero_logic():
    """Test the minute 00 logic specifically"""
    print("\n=== Testing Minute 00 Logic ===")
    
    vm = VerseManager()
    
    # Test different hours at minute 00
    test_times = [
        (10, 0),  # 10:00
        (11, 0),  # 11:00
        (12, 0),  # 12:00
        (13, 0),  # 13:00 (1:00 PM)
    ]
    
    import unittest.mock
    
    for hour, minute in test_times:
        mock_time = datetime(2025, 6, 30, hour, minute, 0)
        
        with unittest.mock.patch('verse_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            print(f"\nTime: {mock_time.strftime('%H:%M')}")
            
            # Call the minute 00 logic directly
            if minute == 0:
                result = vm._get_random_book_summary()
                print(f"  Book: {result['book']}")
                print(f"  Reference: {result['reference']}")
                print(f"  Is summary: {result.get('is_summary', False)}")
            else:
                # Regular verse logic
                verse_data = vm._get_time_based_verse()
                print(f"  Reference: {verse_data.get('reference', 'N/A')}")

def test_jeremiah_book_summary():
    """Test Jeremiah book summary specifically"""
    print("\n=== Testing Jeremiah Book Summary ===")
    
    vm = VerseManager()
    
    # Check if Jeremiah is in book summaries
    if 'Jeremiah' in vm.book_summaries:
        jeremiah_summary = vm.book_summaries['Jeremiah']
        print("Jeremiah summary found:")
        print(f"  Title: {jeremiah_summary['title']}")
        print(f"  Summary: {jeremiah_summary['summary']}")
        
        # Create a book summary data structure like _get_random_book_summary would
        summary_data = {
            'reference': f'Jeremiah - Book Summary',
            'text': jeremiah_summary['summary'],
            'book': 'Jeremiah',
            'chapter': 0,
            'verse': 0,
            'is_summary': True
        }
        
        print("\nGenerated summary data:")
        for key, value in summary_data.items():
            print(f"  {key}: {value}")
        
        # Test what the reference display would show
        print(f"\nReference that would be displayed: '{summary_data['reference']}'")
        
    else:
        print("Jeremiah not found in book summaries!")

if __name__ == "__main__":
    test_book_summary_at_11_00()
    test_minute_zero_logic()
    test_jeremiah_book_summary()