#!/usr/bin/env python3
"""
Test script for the updated bible scraper functionality with web scraping prioritized.
"""

import logging
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from verse_manager import VerseManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_translation_fetching():
    """Test fetching functionality for different translations using the full fallback chain."""
    print("Testing Bible translation fetching with updated fallback chains...")
    print("=" * 70)
    
    # Initialize verse manager
    vm = VerseManager()
    
    # Test translations
    translations_to_test = ['nlt', 'msg', 'esv', 'nasb']
    
    # Test verse
    book = 'John'
    chapter = 3
    verse = 16
    
    for translation in translations_to_test:
        print(f"\nTesting {translation.upper()}...")
        print("-" * 40)
        
        try:
            # Use the full translation fetching system
            result = vm._fetch_verse_from_multi_api(book, chapter, verse, translation)
            
            if result:
                print(f"✅ SUCCESS: {translation.upper()}")
                print(f"Reference: {result['reference']}")
                print(f"Text: {result['text'][:100]}...")
                print(f"Source: {result.get('api_source', 'unknown')}")
                print(f"Translation: {result.get('translation', 'unknown')}")
            else:
                print(f"❌ FAILED: {translation.upper()} - No result returned")
                
        except Exception as e:
            print(f"❌ ERROR: {translation.upper()} - {e}")
    
    print("\n" + "=" * 70)
    print("Test completed. Check logs above for detailed information.")

if __name__ == "__main__":
    test_translation_fetching()