#!/usr/bin/env python3
"""
Test script for the bible scraper functionality with different translations.
"""

import logging
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from verse_manager import VerseManager

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_translation_scraping():
    """Test scraping functionality for different translations."""
    print("Testing Bible Scraper with different translations...")
    print("=" * 60)
    
    # Initialize verse manager
    vm = VerseManager()
    
    # Test translations
    translations_to_test = ['NLT', 'MSG', 'ESV', 'NASB', 'AMP']
    
    # Test verse
    book = 'John'
    chapter = 3
    verse = 16
    
    for translation in translations_to_test:
        print(f"\nTesting {translation}...")
        print("-" * 30)
        
        try:
            result = vm._fetch_from_bible_scraper(book, chapter, verse, translation)
            
            if result:
                print(f"✅ SUCCESS: {translation}")
                print(f"Reference: {result['reference']}")
                print(f"Text: {result['text'][:100]}...")
                print(f"Source: {result['api_source']}")
            else:
                print(f"❌ FAILED: {translation} - No result returned")
                
        except Exception as e:
            print(f"❌ ERROR: {translation} - {e}")
    
    print("\n" + "=" * 60)
    print("Test completed. Check logs above for detailed information.")

if __name__ == "__main__":
    test_translation_scraping()