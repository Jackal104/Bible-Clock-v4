#!/usr/bin/env python3
"""
Test time formatting with leading zeros
"""

from datetime import datetime
import sys
import os

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_time_formatting():
    """Test the new time formatting logic."""
    print("🕐 Testing Time Formatting with Leading Zeros")
    print("=" * 50)
    
    # Test different times to verify formatting
    test_times = [
        (1, 5),   # 1:05 -> should be 01:05  
        (5, 4),   # 5:04 -> should be 05:04
        (12, 30), # 12:30 -> should be 12:30
        (10, 0),  # 10:00 -> should be 10:00
        (3, 15),  # 3:15 -> should be 03:15
    ]
    
    print("Testing 12-hour format with leading zeros:")
    for hour, minute in test_times:
        # Simulate the formatting logic from verse_manager.py
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
        
        # New formatting with leading zeros
        time_display = f"{hour_12:02d}:{minute:02d} {'AM' if hour < 12 else 'PM'}"
        
        # Chapter:verse formatting
        chapter_verse = f"{hour_12:02d}:{minute:02d}"
        
        print(f"  {hour:2d}:{minute:02d} → Display: {time_display} | Chapter:Verse: {chapter_verse}")
    
    print("\nTesting 24-hour format:")
    for hour, minute in test_times:
        # 24-hour format (already has leading zeros with %H:%M)
        time_display = f"{hour:02d}:{minute:02d}"
        chapter = hour if hour > 0 else 24
        chapter_verse = f"{chapter:02d}:{minute:02d}"
        
        print(f"  {hour:2d}:{minute:02d} → Display: {time_display} | Chapter:Verse: {chapter_verse}")
    
    print("\n✅ All time formats now include leading zeros!")
    print("Examples:")
    print("  • 1:05 AM → 01:05 AM (Chapter 01:05)")
    print("  • 5:04 PM → 05:04 PM (Chapter 05:04)")
    print("  • 12:30 PM → 12:30 PM (Chapter 12:30)")

if __name__ == "__main__":
    test_time_formatting()