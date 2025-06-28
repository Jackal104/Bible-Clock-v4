"""
Manages Bible verse retrieval and scheduling.
"""

import json
import random
import requests
import logging
from datetime import datetime, time, date
from pathlib import Path
from typing import Dict, List, Optional
import os
import calendar

class VerseManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_url = os.getenv('BIBLE_API_URL', 'https://bible-api.com')
        self.translation = os.getenv('DEFAULT_TRANSLATION', 'kjv')
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', '10'))
        
        # Enhanced features
        self.display_mode = 'time'  # 'time', 'date', 'random'
        self.parallel_mode = False  # Enable parallel translation mode
        self.secondary_translation = 'web'  # Secondary translation for parallel mode
        self.time_format = '12'  # '12' for 12-hour format, '24' for 24-hour format
        self.statistics = {
            'verses_displayed': 0,
            'verses_today': 0,
            'books_accessed': set(),
            'translation_usage': {},
            'mode_usage': {'time': 0, 'date': 0, 'random': 0}
        }
        self.start_time = datetime.now()
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Load local data
        self._load_fallback_verses()
        self._load_book_summaries()
        self._load_kjv_bible()
        self._load_biblical_calendar()
        self._load_bible_structure()
        
        # All available Bible books (will be populated from local data)
        self.available_books = []
        self._populate_available_books()
    
    def _load_fallback_verses(self):
        """Load fallback verses from JSON file."""
        try:
            fallback_path = Path('data/fallback_verses.json')
            with open(fallback_path, 'r') as f:
                self.fallback_verses = json.load(f)
            self.logger.info(f"Loaded {len(self.fallback_verses)} fallback verses")
        except Exception as e:
            self.logger.error(f"Failed to load fallback verses: {e}")
            self.fallback_verses = self._get_default_fallback_verses()
    
    def _load_book_summaries(self):
        """Load book summaries from JSON file."""
        try:
            summaries_path = Path('data/book_summaries.json')
            with open(summaries_path, 'r') as f:
                self.book_summaries = json.load(f)
            self.logger.info(f"Loaded {len(self.book_summaries)} book summaries")
        except Exception as e:
            self.logger.error(f"Failed to load book summaries: {e}")
            self.book_summaries = {}
    
    def _load_kjv_bible(self):
        """Load complete KJV Bible for offline use."""
        try:
            kjv_path = Path('data/translations/bible_kjv.json')
            with open(kjv_path, 'r') as f:
                self.kjv_bible = json.load(f)
            self.logger.info("Loaded complete KJV Bible")
        except Exception as e:
            self.logger.error(f"Failed to load KJV Bible: {e}")
            self.kjv_bible = {}
    
    def _load_biblical_calendar(self):
        """Load biblical events calendar."""
        try:
            calendar_path = Path('data/biblical_events_calendar.json')
            if calendar_path.exists():
                with open(calendar_path, 'r') as f:
                    calendar_data = json.load(f)
                    self.biblical_events_calendar = calendar_data['biblical_events_calendar']
                self.logger.info(f"Loaded biblical events calendar with events, weekly, monthly, and seasonal themes")
            else:
                self.biblical_events_calendar = self._get_default_biblical_calendar()
            
            # Also keep old calendar for backward compatibility
            try:
                old_calendar_path = Path('data/biblical_calendar.json')
                if old_calendar_path.exists():
                    with open(old_calendar_path, 'r') as f:
                        self.biblical_calendar = json.load(f)
                else:
                    self.biblical_calendar = {}
            except:
                self.biblical_calendar = {}
                
        except Exception as e:
            self.logger.error(f"Failed to load biblical calendar: {e}")
            self.biblical_events_calendar = self._get_default_biblical_calendar()
            self.biblical_calendar = {}
    
    def _load_bible_structure(self):
        """Load complete Bible structure with chapter/verse counts."""
        try:
            structure_path = Path('data/bible_structure.json')
            with open(structure_path, 'r') as f:
                self.bible_structure = json.load(f)
            self.logger.info("Loaded complete Bible structure data")
        except Exception as e:
            self.logger.error(f"Failed to load Bible structure: {e}")
            self.bible_structure = {}
    
    def _populate_available_books(self):
        """Populate the list of available books from local KJV data."""
        # Always use the full list of Bible books for time-based calculations
        # Local KJV data is used for actual verse text when available
        self.available_books = [
            'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
            'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
            '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
            'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs',
            'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah',
            'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel',
            'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk',
            'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
            'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans',
            '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
            'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
            '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
            'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John',
            'Jude', 'Revelation'
        ]
        
        self.logger.info(f"Available books: {len(self.available_books)}")
    
    def _get_books_with_chapter(self, chapter_num: int) -> list:
        """Get list of books that have the specified chapter number."""
        books_with_chapter = []
        
        for book in self.available_books:
            if self.kjv_bible and book in self.kjv_bible:
                # Check local KJV data first
                book_data = self.kjv_bible[book]
                if str(chapter_num) in book_data:
                    books_with_chapter.append(book)
                # If not in local data, use estimates (local data is incomplete)
                elif self._book_likely_has_chapter(book, chapter_num):
                    books_with_chapter.append(book)
            else:
                # For books not in local data, make educated guesses
                if self._book_likely_has_chapter(book, chapter_num):
                    books_with_chapter.append(book)
        
        return books_with_chapter
    
    def _book_likely_has_chapter(self, book: str, chapter_num: int) -> bool:
        """Estimate if a book likely has the given chapter (fallback method)."""
        # Rough estimates for when KJV data isn't available
        book_chapter_estimates = {
            'Psalms': 150, 'Isaiah': 66, 'Jeremiah': 52, 'Genesis': 50,
            'Ezekiel': 48, 'Job': 42, 'Exodus': 40, 'Numbers': 36,
            'Deuteronomy': 34, '1 Chronicles': 29, '2 Chronicles': 36,
            'Matthew': 28, 'Acts': 28, 'Luke': 24, '1 Kings': 22,
            '2 Kings': 25, 'Leviticus': 27, 'Joshua': 24, 'Judges': 21,
            'John': 21, '1 Samuel': 31, '2 Samuel': 24, 'Romans': 16,
            'Mark': 16, '1 Corinthians': 16, '2 Corinthians': 13,
            'Hebrews': 13, 'Revelation': 22, 'Proverbs': 31
        }
        
        estimated_chapters = book_chapter_estimates.get(book, 10)  # Default to 10
        return chapter_num <= estimated_chapters
    
    def _validate_verse_number(self, book: str, chapter: int, verse: int) -> Optional[int]:
        """Validate and adjust verse number using comprehensive Bible structure data."""
        try:
            # Use the complete Bible structure data
            max_verse = self._get_max_verse_for_chapter(book, chapter)
            
            if max_verse is None:
                self.logger.debug(f"No verse data found for {book} {chapter}")
                return None
            
            if verse <= max_verse:
                return verse
            else:
                # Return the highest available verse in this chapter
                self.logger.debug(f"Requested verse {verse} > max {max_verse} for {book} {chapter}, using verse {max_verse}")
                return max_verse
                
        except Exception as e:
            self.logger.debug(f"Verse validation failed for {book} {chapter}:{verse}: {e}")
            return None
    
    def _get_max_verse_for_chapter(self, book: str, chapter: int) -> Optional[int]:
        """Get the maximum verse number for a given book and chapter using complete Bible data."""
        # First check our comprehensive loaded structure
        if hasattr(self, 'bible_structure') and self.bible_structure:
            if book in self.bible_structure:
                book_data = self.bible_structure[book]
                if str(chapter) in book_data:
                    return book_data[str(chapter)]
        
        # Fallback: check local KJV data if available
        if self.kjv_bible and book in self.kjv_bible:
            chapter_data = self.kjv_bible[book].get(str(chapter), {})
            if chapter_data:
                available_verses = [int(v) for v in chapter_data.keys() if v.isdigit()]
                if available_verses:
                    return max(available_verses)
        
        # No data found for this book/chapter
        return None
    
    def _get_all_books_with_valid_verse(self, chapter: int, verse: int) -> List[Dict]:
        """Get all books that have a valid verse for the given chapter:verse, with actual verse numbers."""
        candidate_books = []
        
        # Check all 66 Bible books systematically
        for book in self.available_books:
            # Check if this book has the requested chapter
            if not self._book_has_chapter(book, chapter):
                continue
            
            # Validate and get the actual verse number
            validated_verse = self._validate_verse_number(book, chapter, verse)
            if validated_verse:
                candidate_books.append({
                    'book': book,
                    'verse': validated_verse,
                    'exact_match': validated_verse == verse
                })
        
        # Sort to prioritize exact matches, then by book order
        candidate_books.sort(key=lambda x: (not x['exact_match'], self.available_books.index(x['book'])))
        
        return candidate_books
    
    def _book_has_chapter(self, book: str, chapter: int) -> bool:
        """Check if a book has the specified chapter."""
        if hasattr(self, 'bible_structure') and self.bible_structure:
            if book in self.bible_structure:
                return str(chapter) in self.bible_structure[book]
        
        # Fallback to estimates
        return self._book_likely_has_chapter(book, chapter)
    
    def _get_default_fallback_verses(self) -> List[Dict]:
        """Return default fallback verses if file loading fails."""
        return [
            {
                "reference": "John 3:16",
                "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
                "book": "John",
                "chapter": 3,
                "verse": 16
            },
            {
                "reference": "Psalm 23:1",
                "text": "The LORD is my shepherd; I shall not want.",
                "book": "Psalms",
                "chapter": 23,
                "verse": 1
            },
            {
                "reference": "Romans 8:28",
                "text": "And we know that all things work together for good to them that love God, to them who are the called according to his purpose.",
                "book": "Romans",
                "chapter": 8,
                "verse": 28
            }
        ]
    
    def get_current_verse(self) -> Dict:
        """Get verse based on current display mode."""
        # Check if we need to reset daily counter
        now = datetime.now()
        if now.date() > self.daily_reset_time.date():
            self.statistics['verses_today'] = 0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        self.statistics['verses_displayed'] += 1
        self.statistics['verses_today'] += 1
        
        if self.display_mode == 'date':
            verse_data = self._get_date_based_verse()
        elif self.display_mode == 'random':
            verse_data = self._get_random_verse()
        else:  # time mode
            verse_data = self._get_time_based_verse()
        
        # Add parallel translation if enabled (for all modes)
        if self.parallel_mode and verse_data and not verse_data.get('is_summary') and not verse_data.get('is_date_event'):
            verse_data = self._add_parallel_translation(verse_data)
        
        # Update statistics
        self.statistics['mode_usage'][self.display_mode] += 1
        if verse_data.get('book'):
            self.statistics['books_accessed'].add(verse_data['book'])
        
        translation = getattr(self, 'translation', 'kjv')
        self.statistics['translation_usage'][translation] = self.statistics['translation_usage'].get(translation, 0) + 1
        
        return verse_data
    
    def _get_time_based_verse(self) -> Dict:
        """Time-based verse logic: HH:MM = Chapter:Verse, minute 00 = book summary."""
        now = datetime.now()
        hour_24 = now.hour
        minute = now.minute
        
        # At minute 00, show a book summary
        if minute == 0:
            return self._get_random_book_summary()
        
        # Determine chapter based on time format setting
        if self.time_format == '12':
            # 12-hour format mapping:
            # 00:XX (12:XX AM) = Chapter 12
            # 01:XX (1:XX AM) = Chapter 1, 02:XX (2:XX AM) = Chapter 2, etc.
            # 12:XX (12:XX PM) = Chapter 12  
            # 13:XX (1:XX PM) = Chapter 1, 14:XX (2:XX PM) = Chapter 2, etc.
            if hour_24 == 0:
                chapter = 12  # 12:XX AM = Chapter 12
            elif hour_24 <= 12:
                chapter = hour_24  # 1:XX AM to 12:XX PM = Chapter 1-12
            else:
                chapter = hour_24 - 12  # 1:XX PM to 11:XX PM = Chapter 1-11
        else:  # 24-hour format
            # 24-hour format mapping:
            # 00:XX = Chapter 24, 01:XX = Chapter 1, etc.
            chapter = hour_24 if hour_24 > 0 else 24
        
        verse = minute
        
        verse_data = self._get_verse_from_api(chapter, verse)
        if not verse_data:
            verse_data = self._get_verse_from_local_data(chapter, verse)
        if not verse_data:
            # No exact verse found - check if we should show a summary instead
            verse_data = self._get_time_based_summary_or_fallback(chapter, verse)
        
        return verse_data
    
    def _get_time_based_summary_or_fallback(self, chapter: int, verse: int) -> Dict:
        """Get a time-based book summary when no exact verse exists, or fallback."""
        now = datetime.now()
        
        # Get books that have the requested chapter
        books_with_chapter = []
        for book in self.available_books:
            if self._book_has_chapter(book, chapter):
                books_with_chapter.append(book)
        
        if books_with_chapter:
            # Select a book based on time for consistency
            book_index = (now.hour + now.minute) % len(books_with_chapter)
            selected_book = books_with_chapter[book_index]
            
            # Check if ANY book has the exact verse
            has_exact_verse = any(
                self._validate_verse_number(book, chapter, verse) == verse 
                for book in books_with_chapter
            )
            
            # If no book has the exact verse, show summary instead
            if not has_exact_verse:
                return self._get_time_based_book_summary(selected_book, chapter, verse)
        
        # Final fallback to random verse
        return random.choice(self.fallback_verses)
    
    def _get_time_based_book_summary(self, book: str, chapter: int, verse: int) -> Dict:
        """Get a book summary for time-based display when exact verse doesn't exist."""
        # Get book summary
        if self.book_summaries and book in self.book_summaries:
            summary = self.book_summaries[book]
        else:
            # Create a basic summary if none available
            summary = {
                'title': book,
                'summary': f'{book} is a book of the Bible containing wisdom and spiritual guidance.'
            }
        
        now = datetime.now()
        # Format time with leading zeros for hours
        if self.time_format == '12':
            hour_12 = now.hour % 12
            if hour_12 == 0:
                hour_12 = 12
            time_display = f"{hour_12:02d}:{now.minute:02d} {now.strftime('%p')}"
        else:
            time_display = now.strftime('%H:%M')
        
        return {
            'reference': f'{book} - Book Summary',
            'text': summary['summary'],
            'book': book,
            'chapter': 0,  # 0 indicates summary
            'verse': 0,    # 0 indicates summary
            'is_summary': True,
            'is_time_based_summary': True,
            'requested_time': f'{chapter:02d}:{verse:02d}',
            'current_time': time_display,
            'summary_reason': f'No Bible book contains Chapter {chapter:02d}, Verse {verse:02d}',
            'time_correlation': f'Time {time_display} → Chapter {chapter:02d}:Verse {verse:02d} → {book} Summary'
        }
    
    def _get_date_based_verse(self) -> Dict:
        """Get verse based on today's date and biblical events with 15-minute cycling."""
        now = datetime.now()
        today = now.date()
        
        # Calculate which verse to show based on 15-minute intervals
        # This gives us 4 verses per hour, 96 verse slots per day
        quarter_hour = now.minute // 15  # 0, 1, 2, or 3
        hour = now.hour
        verse_index = (hour * 4) + quarter_hour  # 0-95
        
        # First, try to get verses for exact date (MM-DD format)
        date_key = f"{today.month:02d}-{today.day:02d}"
        available_verses = []
        match_type = "exact"
        event_info = None
        
        if date_key in self.biblical_events_calendar.get('events', {}):
            events = self.biblical_events_calendar['events'][date_key]
            for event in events:
                event_info = event
                available_verses.extend(event['verses'])
        
        # If no exact date match, try weekly theme
        if not available_verses:
            weekday_name = calendar.day_name[today.weekday()].lower()
            weekly_themes = self.biblical_events_calendar.get('weekly_themes', {})
            if weekday_name in weekly_themes:
                for theme in weekly_themes[weekday_name]:
                    event_info = theme
                    available_verses.extend(theme['verses'])
                match_type = "weekly"
        
        # If no weekly match, try monthly theme
        if not available_verses:
            month_name = calendar.month_name[today.month].lower()
            monthly_themes = self.biblical_events_calendar.get('monthly_themes', {})
            if month_name in monthly_themes:
                for theme in monthly_themes[month_name]:
                    event_info = theme
                    available_verses.extend(theme['verses'])
                match_type = "monthly"
        
        # If no monthly match, try seasonal theme
        if not available_verses:
            season = self._get_current_season(today)
            seasonal_themes = self.biblical_events_calendar.get('seasonal_themes', {})
            if season in seasonal_themes:
                for theme in seasonal_themes[season]:
                    event_info = theme
                    available_verses.extend(theme['verses'])
                match_type = "seasonal"
        
        # If we have verses, cycle through them based on time
        if available_verses:
            verse = available_verses[verse_index % len(available_verses)]
            
            # Parse reference to extract book, chapter, verse
            ref_parts = verse['reference'].split()
            book = ref_parts[0]
            if len(ref_parts) > 1 and ':' in ref_parts[-1]:
                chapter_verse = ref_parts[-1].split(':')
                chapter = int(chapter_verse[0]) if chapter_verse[0].isdigit() else 1
                verse_num = int(chapter_verse[1]) if len(chapter_verse) > 1 and chapter_verse[1].isdigit() else 1
            else:
                chapter = 1
                verse_num = 1
            
            return {
                'reference': verse['reference'],
                'text': verse['text'],
                'book': book,
                'chapter': chapter,
                'verse': verse_num,
                'is_date_event': True,
                'event_name': event_info.get('title', f"Biblical Event for {today.strftime('%B %d')}"),
                'event_description': event_info.get('description', 'Biblical wisdom for today'),
                'date_match': match_type,
                'verse_cycle_position': f"{verse_index % len(available_verses) + 1} of {len(available_verses)}",
                'next_verse_minutes': 15 - (now.minute % 15)
            }
        
        # Ultimate fallback to random verse with date context
        fallback = random.choice(self.fallback_verses)
        fallback['is_date_event'] = True
        fallback['event_name'] = f"Daily Blessing for {today.strftime('%B %d')}"
        fallback['event_description'] = "God's word for today"
        fallback['date_match'] = 'fallback'
        fallback['verse_cycle_position'] = "1 of 1"
        fallback['next_verse_minutes'] = 15 - (now.minute % 15)
        
        return fallback
    
    def _add_parallel_translation(self, verse_data: Dict) -> Dict:
        """Add parallel translation to verse data."""
        try:
            book = verse_data.get('book')
            chapter = verse_data.get('chapter')
            verse = verse_data.get('verse')
            
            if not all([book, chapter, verse]):
                return verse_data
            
            # Try to get secondary translation from API
            secondary_verse = self._get_verse_from_api_with_translation(
                book, chapter, verse, self.secondary_translation
            )
            
            if secondary_verse:
                verse_data['parallel_mode'] = True
                verse_data['primary_translation'] = self.translation.upper()
                verse_data['secondary_translation'] = self.secondary_translation.upper()
                verse_data['secondary_text'] = secondary_verse['text']
            
            return verse_data
            
        except Exception as e:
            self.logger.warning(f"Failed to get parallel translation: {e}")
            return verse_data
    
    def _get_verse_from_api_with_translation(self, book: str, chapter: int, verse: int, translation: str) -> Optional[Dict]:
        """Get verse from API with specific translation and validation."""
        if not self.api_url:
            return None
        
        try:
            # Validate the verse exists for this book/chapter
            validated_verse = self._validate_verse_number(book, chapter, verse)
            if not validated_verse:
                self.logger.debug(f"Verse {book} {chapter}:{verse} not valid for parallel translation")
                return None
            
            actual_verse = validated_verse
            url = f"{self.api_url}/{book} {chapter}:{actual_verse}"
            if translation != 'kjv':
                url += f"?translation={translation}"
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            verse_text = data.get('text', '').strip()
            
            if not verse_text:
                return None
            
            return {
                'reference': data.get('reference', f"{book} {chapter:02d}:{actual_verse:02d}"),
                'text': verse_text,
                'book': book,
                'chapter': chapter,
                'verse': actual_verse,
                'translation': translation,
                'adjusted': actual_verse != verse
            }
            
        except Exception as e:
            self.logger.debug(f"API request failed for {translation} {book} {chapter}:{verse}: {e}")
            return None
    
    def _get_random_verse(self) -> Dict:
        """Get a completely random verse."""
        return random.choice(self.fallback_verses)
    
    def _get_random_book_summary(self) -> Dict:
        """Get a random book summary."""
        if self.book_summaries:
            book = random.choice(list(self.book_summaries.keys()))
            summary = self.book_summaries[book]
        else:
            # Fallback if no summaries available
            book = random.choice(self.available_books)
            summary = {
                'title': book,
                'summary': f'{book} is a book of the Bible containing wisdom and spiritual guidance.'
            }
        
        return {
            'reference': f'{book} - Book Summary',
            'text': summary['summary'],
            'book': book,
            'chapter': 0,
            'verse': 0,
            'is_summary': True
        }
    
    def _get_verse_from_api(self, chapter: int, verse: int) -> Optional[Dict]:
        """Get verse from API using systematic book selection and comprehensive validation."""
        if not self.api_url:
            return None
        
        try:
            # Get all books that have this chapter systematically
            all_candidate_books = self._get_all_books_with_valid_verse(chapter, verse)
            
            if not all_candidate_books:
                self.logger.debug(f"No books found with valid verse {chapter}:{verse}")
                return None
            
            # Prioritize books with exact verse match, then use time-based selection
            exact_match_books = [book for book in all_candidate_books if book['exact_match']]
            
            if exact_match_books:
                # Use time-based selection among books with exact verse match
                now = datetime.now()
                book_index = (now.hour + now.minute) % len(exact_match_books)
                selected_book_data = exact_match_books[book_index]
                self.logger.debug(f"Selected exact match: {selected_book_data['book']} {chapter}:{selected_book_data['verse']}")
            else:
                # Fall back to any valid book
                now = datetime.now()
                book_index = (now.hour + now.minute) % len(all_candidate_books)
                selected_book_data = all_candidate_books[book_index]
                self.logger.debug(f"Selected adjusted verse: {selected_book_data['book']} {chapter}:{selected_book_data['verse']} (requested {verse})")
            
            book = selected_book_data['book']
            actual_verse = selected_book_data['verse']
            
            url = f"{self.api_url}/{book} {chapter}:{actual_verse}"
            if self.translation != 'kjv':
                url += f"?translation={self.translation}"
            
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                verse_text = data.get('text', '').strip()
                
                if verse_text:
                    return {
                        'reference': data.get('reference', f"{book} {chapter:02d}:{actual_verse:02d}"),
                        'text': verse_text,
                        'book': book,
                        'chapter': chapter,
                        'verse': actual_verse,
                        'original_request': f"{chapter}:{verse}",
                        'adjusted': actual_verse != verse
                    }
                else:
                    self.logger.debug(f"Empty verse returned from API for {book} {chapter}:{actual_verse}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.debug(f"API request failed for {book} {chapter}:{actual_verse}: {e}")
                return None
            
            return None
            
        except Exception as e:
            self.logger.warning(f"API request failed: {e}")
            return None
    
    def _get_verse_from_local_data(self, chapter: int, verse: int) -> Optional[Dict]:
        """Get verse from local KJV data."""
        try:
            # Get books that have the required chapter
            books_with_chapter = self._get_books_with_chapter(chapter)
            
            if not books_with_chapter:
                self.logger.warning(f"No books found with chapter {chapter}")
                return None
            
            # Try each book until we find one with the verse
            random.shuffle(books_with_chapter)  # Randomize the order
            
            for book in books_with_chapter:
                book_data = self.kjv_bible.get(book, {})
                chapter_data = book_data.get(str(chapter), {})
                verse_text = chapter_data.get(str(verse))
                
                if verse_text:
                    return {
                        'reference': f"{book} {chapter:02d}:{verse:02d}",
                        'text': verse_text,
                        'book': book,
                        'chapter': chapter,
                        'verse': verse
                    }
            
            # If exact verse not found, try to find a verse in the chapter
            for book in books_with_chapter:
                book_data = self.kjv_bible.get(book, {})
                chapter_data = book_data.get(str(chapter), {})
                
                if chapter_data:
                    # Get the highest verse number available in this chapter
                    available_verses = [int(v) for v in chapter_data.keys() if v.isdigit()]
                    if available_verses:
                        # Use the verse number closest to what we want, but not exceeding it
                        suitable_verses = [v for v in available_verses if v <= verse]
                        if suitable_verses:
                            actual_verse = max(suitable_verses)
                        else:
                            actual_verse = min(available_verses)
                        
                        verse_text = chapter_data[str(actual_verse)]
                        
                        return {
                            'reference': f"{book} {chapter:02d}:{actual_verse:02d}",
                            'text': verse_text,
                            'book': book,
                            'chapter': chapter,
                            'verse': actual_verse
                        }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Local data lookup failed: {e}")
            return None
    
    def _get_week_events(self, target_date: date) -> List[Dict]:
        """Get events from the same week of the year."""
        target_week = target_date.isocalendar()[1]
        week_events = []
        
        for date_key, event in self.biblical_calendar.items():
            try:
                month, day = map(int, date_key.split('-'))
                event_date = date(target_date.year, month, day)
                event_week = event_date.isocalendar()[1]
                
                if abs(event_week - target_week) <= 1:  # Same or adjacent week
                    week_events.append(event)
            except (ValueError, TypeError):
                continue
        
        return week_events
    
    def _get_month_events(self, target_month: int) -> List[Dict]:
        """Get events from the same month."""
        month_events = []
        
        for date_key, event in self.biblical_calendar.items():
            try:
                month, day = map(int, date_key.split('-'))
                if month == target_month:
                    month_events.append(event)
            except (ValueError, TypeError):
                continue
        
        return month_events
    
    def _get_season_event(self, target_date: date) -> Optional[Dict]:
        """Get event based on current season."""
        # Determine season
        month = target_date.month
        day = target_date.day
        
        if (month == 12 and day >= 21) or month in [1, 2] or (month == 3 and day < 20):
            season = "winter"
            season_key = "12-21"  # Winter solstice
        elif (month == 3 and day >= 20) or month in [4, 5] or (month == 6 and day < 21):
            season = "spring"
            season_key = "3-21"  # Spring equinox
        elif (month == 6 and day >= 21) or month in [7, 8] or (month == 9 and day < 22):
            season = "summer"
            season_key = "6-21"  # Summer solstice
        else:
            season = "autumn"
            season_key = "9-22"  # Autumn equinox
        
        return self.biblical_calendar.get(season_key)
    
    def _get_default_biblical_calendar(self):
        """Default biblical calendar events."""
        return {
            "1-1": {
                "event": "New Year - God's Covenant Renewal",
                "reference": "Lamentations 3:22-23",
                "text": "It is of the LORD'S mercies that we are not consumed, because his compassions fail not. They are new every morning: great is thy faithfulness.",
                "description": "God's mercies are renewed each morning, making New Year a time of fresh beginnings."
            },
            "12-25": {
                "event": "Christmas - Birth of Christ",
                "reference": "Luke 2:11",
                "text": "For unto you is born this day in the city of David a Saviour, which is Christ the Lord.",
                "description": "The birth of Jesus Christ, our Savior and Lord."
            },
            "6-21": {
                "event": "Summer Solstice - God's Light",
                "reference": "Psalm 84:11",
                "text": "For the LORD God is a sun and shield: the LORD will give grace and glory: no good thing will he withhold from them that walk uprightly.",
                "description": "The longest day celebrates God as our light and source of life."
            }
        }
    
    def get_statistics(self) -> Dict:
        """Get usage statistics."""
        stats = self.statistics.copy()
        stats['books_accessed'] = list(stats['books_accessed'])
        stats['uptime'] = self.start_time.isoformat()
        
        return stats
    
    def set_display_mode(self, mode: str):
        """Set display mode."""
        if mode in ['time', 'date', 'random']:
            self.display_mode = mode
            self.logger.info(f"Display mode changed to: {mode}")
        else:
            raise ValueError(f"Invalid display mode: {mode}")
    
    def _add_parallel_translation(self, verse_data: Dict) -> Dict:
        """Add secondary translation for parallel mode."""
        if not verse_data or not hasattr(self, 'secondary_translation'):
            return verse_data
        
        try:
            # Extract book, chapter, verse from primary verse
            book = verse_data['book']
            chapter = verse_data['chapter']
            verse = verse_data['verse']
            
            # Try to get the same verse in secondary translation
            url = f"{self.api_url}/{book} {chapter}:{verse}"
            if self.secondary_translation != 'kjv':
                url += f"?translation={self.secondary_translation}"
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            secondary_data = response.json()
            secondary_text = secondary_data.get('text', '').strip()
            
            if secondary_text:
                verse_data['parallel_mode'] = True
                verse_data['secondary_text'] = secondary_text
                verse_data['primary_translation'] = self.translation.upper()
                verse_data['secondary_translation'] = self.secondary_translation.upper()
                self.logger.info(f"Added parallel translation: {self.secondary_translation}")
            else:
                self.logger.warning(f"Empty secondary translation for {book} {chapter}:{verse}")
                
        except Exception as e:
            self.logger.warning(f"Failed to get parallel translation: {e}")
            # Continue with single translation
            
        return verse_data

    def _get_current_season(self, today):
        """Get the current season based on the date."""
        month = today.month
        day = today.day
        
        # Spring: March 20 - June 20
        if (month == 3 and day >= 20) or (month in [4, 5]) or (month == 6 and day < 21):
            return 'spring'
        # Summer: June 21 - September 21
        elif (month == 6 and day >= 21) or (month in [7, 8]) or (month == 9 and day < 22):
            return 'summer'
        # Autumn/Fall: September 22 - December 20
        elif (month == 9 and day >= 22) or (month in [10, 11]) or (month == 12 and day < 21):
            return 'autumn'
        # Winter: December 21 - March 19
        else:
            return 'winter'


class VerseScheduler:
    """Handles scheduling of verse updates."""
    
    def __init__(self, verse_manager: VerseManager, update_callback):
        self.verse_manager = verse_manager
        self.update_callback = update_callback
        self.logger = logging.getLogger(__name__)
    
    def schedule_updates(self):
        """Schedule verse updates at the start of each minute."""
        import schedule
        
        schedule.every().minute.at(":00").do(self._update_verse)
        self.logger.info("Verse updates scheduled")
    
    def _update_verse(self):
        """Update the displayed verse."""
        try:
            verse_data = self.verse_manager.get_current_verse()
            self.update_callback(verse_data)
        except Exception as e:
            self.logger.error(f"Verse update failed: {e}")