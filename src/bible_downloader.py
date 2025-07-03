#!/usr/bin/env python3
"""
Bible Translation Downloader and Converter
Downloads complete Bible translations from public sources and converts them to the format expected by Bible Clock.
"""

import json
import requests
import os
from pathlib import Path
import logging
from typing import Dict, Any, Optional, List
import time

class BibleDownloader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.translation_dir = Path('data/translations')
        self.translation_dir.mkdir(parents=True, exist_ok=True)
        
        # KJV Bible books from GitHub repository - all 66 books
        self.kjv_books = [
            "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
            "1Samuel", "2Samuel", "1Kings", "2Kings", "1Chronicles", "2Chronicles", "Ezra", "Nehemiah",
            "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "SongofSolomon", "Isaiah", "Jeremiah",
            "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
            "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew", "Mark",
            "Luke", "John", "Acts", "Romans", "1Corinthians", "2Corinthians", "Galatians", "Ephesians",
            "Philippians", "Colossians", "1Thessalonians", "2Thessalonians", "1Timothy", "2Timothy",
            "Titus", "Philemon", "Hebrews", "James", "1Peter", "2Peter", "1John", "2John", "3John",
            "Jude", "Revelation"
        ]
        
        # Map GitHub book names to our standard book names
        self.book_name_mapping = {
            "1Samuel": "1 Samuel",
            "2Samuel": "2 Samuel", 
            "1Kings": "1 Kings",
            "2Kings": "2 Kings",
            "1Chronicles": "1 Chronicles",
            "2Chronicles": "2 Chronicles",
            "SongofSolomon": "Song of Songs",
            "1Corinthians": "1 Corinthians",
            "2Corinthians": "2 Corinthians",
            "1Thessalonians": "1 Thessalonians",
            "2Thessalonians": "2 Thessalonians",
            "1Timothy": "1 Timothy",
            "2Timothy": "2 Timothy",
            "1Peter": "1 Peter",
            "2Peter": "2 Peter",
            "1John": "1 John",
            "2John": "2 John",
            "3John": "3 John"
        }

    def download_kjv_complete(self) -> bool:
        """Download complete KJV Bible from GitHub and convert to our format."""
        self.logger.info("Starting KJV Bible download from GitHub...")
        
        kjv_bible = {}
        total_books = len(self.kjv_books)
        
        for i, book in enumerate(self.kjv_books, 1):
            try:
                self.logger.info(f"Downloading {book} ({i}/{total_books})...")
                
                # Download from GitHub
                url = f"https://raw.githubusercontent.com/aruljohn/Bible-kjv/master/{book}.json"
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Parse JSON
                book_data = response.json()
                
                # Convert to our format
                book_name = self.book_name_mapping.get(book, book)
                kjv_bible[book_name] = self._convert_kjv_book_format(book_data)
                
                self.logger.info(f"Successfully converted {book_name}")
                
                # Small delay to be respectful to GitHub
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Failed to download {book}: {e}")
                return False
        
        # Save complete KJV Bible
        try:
            kjv_path = self.translation_dir / 'bible_kjv.json'
            with open(kjv_path, 'w', encoding='utf-8') as f:
                json.dump(kjv_bible, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Successfully saved complete KJV Bible to {kjv_path}")
            self._log_bible_stats(kjv_bible, "KJV")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save KJV Bible: {e}")
            return False

    def _convert_kjv_book_format(self, book_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Convert GitHub KJV format to our expected format."""
        converted_book = {}
        
        for chapter_data in book_data.get('chapters', []):
            chapter_num = chapter_data['chapter']
            converted_book[chapter_num] = {}
            
            for verse_data in chapter_data.get('verses', []):
                verse_num = verse_data['verse']
                verse_text = verse_data['text']
                converted_book[chapter_num][verse_num] = verse_text
        
        return converted_book

    def download_web_bible(self, translation: str = 'web') -> bool:
        """Download World English Bible from getBible API."""
        self.logger.info(f"Starting {translation.upper()} Bible download from getBible API...")
        
        try:
            # Get Bible from getBible API
            url = f"https://getbible.net/v2/{translation}/json"
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            bible_data = response.json()
            
            # Convert to our format
            converted_bible = self._convert_getbible_format(bible_data)
            
            # Save to file
            file_path = self.translation_dir / f'bible_{translation}.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(converted_bible, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Successfully saved {translation.upper()} Bible to {file_path}")
            self._log_bible_stats(converted_bible, translation.upper())
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download {translation.upper()} Bible: {e}")
            return False

    def _convert_getbible_format(self, bible_data: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Convert getBible API format to our expected format."""
        converted_bible = {}
        
        for book_key, book_data in bible_data.items():
            if not isinstance(book_data, dict) or 'name' not in book_data:
                continue
                
            book_name = book_data['name']
            converted_book = {}
            
            for chapter_key, chapter_data in book_data.items():
                if chapter_key == 'name' or not isinstance(chapter_data, dict):
                    continue
                    
                chapter_num = str(chapter_key)
                converted_chapter = {}
                
                for verse_key, verse_data in chapter_data.items():
                    if not isinstance(verse_data, dict) or 'text' not in verse_data:
                        continue
                        
                    verse_num = str(verse_key)
                    verse_text = verse_data['text']
                    converted_chapter[verse_num] = verse_text
                
                if converted_chapter:
                    converted_book[chapter_num] = converted_chapter
            
            if converted_book:
                converted_bible[book_name] = converted_book
        
        return converted_bible

    def download_bible_supserearch_json(self, translation: str = 'kjv') -> bool:
        """Download Bible from Bible SuperSearch JSON format."""
        self.logger.info(f"Attempting to download {translation.upper()} from Bible SuperSearch...")
        
        # Bible SuperSearch direct download URLs
        translation_urls = {
            'kjv': 'https://sourceforge.net/projects/biblesuper/files/All%20Bibles%20-%20JSON/kjv.json/download',
            'asv': 'https://sourceforge.net/projects/biblesuper/files/All%20Bibles%20-%20JSON/asv.json/download',
            'ylt': 'https://sourceforge.net/projects/biblesuper/files/All%20Bibles%20-%20JSON/ylt.json/download'
        }
        
        if translation not in translation_urls:
            self.logger.error(f"Translation {translation} not available from Bible SuperSearch")
            return False
        
        try:
            url = translation_urls[translation]
            response = requests.get(url, timeout=120, allow_redirects=True)
            response.raise_for_status()
            
            bible_data = response.json()
            
            # Convert format (assuming it matches getBible format)
            converted_bible = self._convert_supersearch_format(bible_data)
            
            # Save to file
            file_path = self.translation_dir / f'bible_{translation}.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(converted_bible, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Successfully saved {translation.upper()} Bible to {file_path}")
            self._log_bible_stats(converted_bible, translation.upper())
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download {translation.upper()} from Bible SuperSearch: {e}")
            return False

    def _convert_supersearch_format(self, bible_data: Any) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Convert Bible SuperSearch JSON format to our expected format."""
        # This will depend on the actual format from Bible SuperSearch
        # For now, assume it's similar to getBible format
        if isinstance(bible_data, dict):
            return self._convert_getbible_format(bible_data)
        else:
            # Handle other possible formats
            self.logger.warning("Unknown Bible SuperSearch format, attempting generic conversion")
            return {}

    def _log_bible_stats(self, bible: Dict[str, Any], translation: str):
        """Log statistics about the downloaded Bible."""
        book_count = len(bible)
        chapter_count = sum(len(book.get('chapters', book)) for book in bible.values() if isinstance(book, dict))
        verse_count = 0
        
        for book in bible.values():
            if isinstance(book, dict):
                for chapter in book.values():
                    if isinstance(chapter, dict):
                        verse_count += len(chapter)
        
        self.logger.info(f"{translation} Bible stats: {book_count} books, ~{chapter_count} chapters, ~{verse_count} verses")

    def download_all_available(self):
        """Download all available free Bible translations."""
        self.logger.info("Starting download of all available Bible translations...")
        
        success_count = 0
        
        # Download KJV from GitHub (most reliable)
        if self.download_kjv_complete():
            success_count += 1
        
        # Note: WEB translation removed from download process
        
        # Try Bible SuperSearch translations
        for translation in ['asv', 'ylt']:
            if self.download_bible_supserearch_json(translation):
                success_count += 1
        
        self.logger.info(f"Successfully downloaded {success_count} Bible translations")
        return success_count > 0


def main():
    """Main function to run the Bible downloader."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    downloader = BibleDownloader()
    
    print("Bible Translation Downloader")
    print("=" * 40)
    print("1. Download KJV from GitHub")
    print("2. Download Other Translations (WEB removed)")
    print("3. Download all available translations")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            downloader.download_kjv_complete()
        elif choice == '2':
            print("WEB translation download removed - choose option 3 for other translations")
        elif choice == '3':
            downloader.download_all_available()
        elif choice == '4':
            print("Exiting...")
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nDownload cancelled by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()