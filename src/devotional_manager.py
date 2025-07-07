"""
Devotional Manager for Bible Clock
Manages daily devotional content from various sources, primarily Faith's Checkbook by Charles Spurgeon
"""

import json
import logging
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import calendar
import re
from bs4 import BeautifulSoup

class DevotionalManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.devotional_cache_dir = Path('data/devotionals')
        self.devotional_cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = 30
        
        # Cache settings
        self.devotional_cache_enabled = True
        self.max_cache_age_days = 30
        
        # Configurable interval settings
        self.default_rotation_minutes = 15  # Default interval
        self.config_file = Path('data/devotional_config.json')
        self._load_config()
        
        # Devotional sources
        self.sources = {
            'faiths_checkbook': {
                'name': "Faith's Checkbook",
                'author': 'Charles Spurgeon',
                'base_url': 'https://www.crosswalk.com/devotionals/faithcheckbook/',
                'enabled': True
            }
        }
        
        # Load existing devotional cache
        self._load_devotional_cache()
        
        self.logger.info("DevotionalManager initialized")

    def _load_config(self):
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.rotation_minutes = config.get('rotation_minutes', self.default_rotation_minutes)
                    self.logger.info(f"Loaded devotional config: rotation_minutes={self.rotation_minutes}")
            else:
                self.rotation_minutes = self.default_rotation_minutes
                self._save_config()
                self.logger.info(f"Created default devotional config: rotation_minutes={self.rotation_minutes}")
        except Exception as e:
            self.logger.error(f"Error loading devotional config: {e}")
            self.rotation_minutes = self.default_rotation_minutes

    def _save_config(self):
        """Save configuration to file."""
        try:
            config = {
                'rotation_minutes': self.rotation_minutes,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.logger.debug("Saved devotional configuration")
        except Exception as e:
            self.logger.error(f"Error saving devotional config: {e}")

    def set_rotation_interval(self, minutes: int):
        """Set the rotation interval in minutes."""
        if minutes < 1 or minutes > 1440:  # Max 24 hours
            raise ValueError("Rotation interval must be between 1 and 1440 minutes")
        
        self.rotation_minutes = minutes
        self._save_config()
        self.logger.info(f"Updated devotional rotation interval to {minutes} minutes")

    def get_rotation_interval(self) -> int:
        """Get the current rotation interval in minutes."""
        return self.rotation_minutes

    def _load_devotional_cache(self):
        """Load existing cached devotionals from file."""
        try:
            cache_file = self.devotional_cache_dir / 'faiths_checkbook_cache.json'
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.devotional_cache = json.load(f)
                self.logger.info(f"Loaded {len(self.devotional_cache)} cached devotionals")
            else:
                self.devotional_cache = {}
                self.logger.info("No existing devotional cache found, starting fresh")
        except Exception as e:
            self.logger.error(f"Error loading devotional cache: {e}")
            self.devotional_cache = {}

    def _save_devotional_cache(self):
        """Save devotional cache to file."""
        try:
            cache_file = self.devotional_cache_dir / 'faiths_checkbook_cache.json'
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.devotional_cache, f, indent=2, ensure_ascii=False)
            self.logger.debug("Saved devotional cache to file")
        except Exception as e:
            self.logger.error(f"Error saving devotional cache: {e}")

    def get_today_devotional(self, source: str = 'faiths_checkbook') -> Optional[Dict[str, Any]]:
        """Get today's devotional."""
        today = datetime.now()
        return self.get_devotional_by_date(today, source)

    def get_rotating_devotional(self, source: str = 'faiths_checkbook', rotation_minutes: int = None) -> Optional[Dict[str, Any]]:
        """Get devotional that rotates every specified number of minutes with random selection."""
        now = datetime.now()
        
        # Use configured interval if no override provided
        if rotation_minutes is None:
            rotation_minutes = self.rotation_minutes
        
        # Calculate which rotation slot we're in
        minutes_since_midnight = now.hour * 60 + now.minute
        rotation_slot = minutes_since_midnight // rotation_minutes
        
        # Get random devotional from cache using slot as seed for consistency during the interval
        devotional = self._get_random_devotional_from_cache(rotation_slot)
        
        if devotional:
            # Add rotation metadata
            devotional['rotation_slot'] = rotation_slot
            devotional['rotation_minutes'] = rotation_minutes
            devotional['next_change_at'] = self._get_next_rotation_time(now, rotation_minutes).strftime('%H:%M')
            # Add time and date for display
            devotional['current_time'] = now.strftime('%I:%M %p')
            devotional['current_date'] = now.strftime('%A, %B %d, %Y')
            
        return devotional

    def _get_random_devotional_from_cache(self, slot: int) -> Optional[Dict[str, Any]]:
        """Get a random devotional from cache using slot as seed for consistency."""
        import random
        
        if not self.devotional_cache:
            return None
        
        cache_keys = list(self.devotional_cache.keys())
        if not cache_keys:
            return None
        
        # Use slot to randomly select devotional with proper randomization
        # This ensures truly random devotionals are shown in different time slots
        random.seed(slot)  # Use slot as seed for consistency within the same time slot
        selected_index = random.randint(0, len(cache_keys) - 1)
        selected_key = cache_keys[selected_index]
        
        devotional = self.devotional_cache[selected_key].copy()
        
        # Clean up the devotional text - remove unwanted content
        if 'devotional_text' in devotional:
            devotional['devotional_text'] = self._clean_devotional_text(devotional['devotional_text'])
        
        # Add debug info for cycling
        devotional['cache_position'] = f"{selected_index + 1} of {len(cache_keys)}"
        devotional['rotation_info'] = f"Slot {slot}, showing devotional {selected_index + 1}/{len(cache_keys)}"
        
        return devotional

    def _clean_devotional_text(self, text: str) -> str:
        """Clean up devotional text by removing unwanted content."""
        # Remove purchase messages and archive links (enhanced patterns)
        text = re.sub(r'Purchase your own copy of this devotional\..*?$', '', text, flags=re.MULTILINE | re.DOTALL)
        text = re.sub(r'Or, catch up on.*?Archives\..*?$', '', text, flags=re.MULTILINE | re.DOTALL)
        text = re.sub(r'catch up on.*?Archives\..*?$', '', text, flags=re.MULTILINE | re.DOTALL)
        
        # Additional purchase/archive removal patterns
        text = re.sub(r'Purchase.*?devotional.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'Buy.*?copy.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'Order.*?devotional.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'Visit.*?archive.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'Check.*?archive.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'.*?archives?\..*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'Available.*?store.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'.*?bookstore.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Comprehensive date removal patterns
        # Remove dates from beginning (e.g., "July 3", "June 26", etc.)
        text = re.sub(r'^[A-Z][a-z]+ \d+', '', text)
        
        # Remove additional date patterns at start of text
        text = re.sub(r'^[A-Z][a-z]+ \d{1,2}[a-z]{0,2}[,\s]*', '', text)
        text = re.sub(r'^\d{1,2}[a-z]{0,2} [A-Z][a-z]+[,\s]*', '', text)
        text = re.sub(r'^[A-Z][a-z]+ \d{1,2}[a-z]{0,2}[,\s]*\d{4}', '', text)
        
        # Remove dates anywhere in text (more comprehensive)
        text = re.sub(r'\b[A-Z][a-z]+ \d{1,2}[a-z]{0,2}[,\s]*\d{4}\b', '', text)
        text = re.sub(r'\b\d{1,2}[a-z]{0,2} [A-Z][a-z]+[,\s]*\d{4}\b', '', text)
        text = re.sub(r'\b[A-Z][a-z]+ \d{1,2}[a-z]{0,2}\b', '', text)
        text = re.sub(r'\b\d{1,2}[a-z]{0,2} [A-Z][a-z]+\b', '', text)
        
        # Remove numeric date patterns (MM/DD/YYYY, DD/MM/YYYY, etc.)
        text = re.sub(r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b', '', text)
        text = re.sub(r'\b\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\b', '', text)
        
        # Remove rotation information
        text = re.sub(r'Next rotation:.*?$', '', text, flags=re.MULTILINE)
        text = re.sub(r'Rotation \d+/\d+.*?$', '', text, flags=re.MULTILINE)
        
        # Remove pagination references
        text = re.sub(r'pages?\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'page\s+\d+', '', text, flags=re.IGNORECASE)
        
        # Remove time references that might be in devotional text
        text = re.sub(r'\b\d{1,2}:\d{2}(?::\d{2})?\s*[AP]M\b', '', text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and punctuation artifacts
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'^\s*[,\.\-]\s*', '', text)  # Remove leading punctuation
        text = re.sub(r'\s*[,\.\-]\s*$', '', text)  # Remove trailing punctuation
        
        return text

    def _get_next_rotation_time(self, current_time: datetime, rotation_minutes: int) -> datetime:
        """Calculate when the next rotation will occur."""
        minutes_since_midnight = current_time.hour * 60 + current_time.minute
        current_slot = minutes_since_midnight // rotation_minutes
        next_slot_start = (current_slot + 1) * rotation_minutes
        
        # Handle day rollover
        if next_slot_start >= 24 * 60:  # If next slot is tomorrow
            next_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            return next_day
        else:
            hours = next_slot_start // 60
            minutes = next_slot_start % 60
            return current_time.replace(hour=hours, minute=minutes, second=0, microsecond=0)

    def get_devotional_by_date(self, date: datetime, source: str = 'faiths_checkbook') -> Optional[Dict[str, Any]]:
        """Get devotional for a specific date."""
        if source not in self.sources:
            self.logger.error(f"Unknown devotional source: {source}")
            return None
        
        # Create cache key
        cache_key = f"{source}_{date.month:02d}_{date.day:02d}"
        
        # Check cache first
        if cache_key in self.devotional_cache:
            cached_devotional = self.devotional_cache[cache_key]
            # Check if cache is still fresh
            cache_date = datetime.fromisoformat(cached_devotional.get('cached_date', '1970-01-01'))
            if datetime.now() - cache_date < timedelta(days=self.max_cache_age_days):
                self.logger.debug(f"Returning cached devotional for {date.strftime('%B %d')}")
                return cached_devotional
        
        # Fetch new devotional
        if source == 'faiths_checkbook':
            devotional = self._fetch_faiths_checkbook_devotional(date)
        else:
            self.logger.error(f"Unsupported devotional source: {source}")
            return None
        
        # Cache the result if successful
        if devotional and self.devotional_cache_enabled:
            devotional['cached_date'] = datetime.now().isoformat()
            self.devotional_cache[cache_key] = devotional
            self._save_devotional_cache()
        
        return devotional

    def _fetch_faiths_checkbook_devotional(self, date: datetime) -> Optional[Dict[str, Any]]:
        """Fetch Faith's Checkbook devotional for a specific date."""
        try:
            # Try multiple URL patterns for Faith's Checkbook
            month_name = date.strftime('%B').lower()
            month_abbr = date.strftime('%b').lower()
            day = date.day
            
            # Common URL patterns to try
            url_patterns = [
                f"https://www.crosswalk.com/devotionals/faithcheckbook/faiths-checkbook-{month_name}-{day}-{date.year}.html",
                f"https://www.christianity.com/devotionals/faiths-checkbook-ch-spurgeon/{month_abbr}-{day:02d}-{date.year}.html",
                f"https://www.christianity.com/devotionals/faiths-checkbook-ch-spurgeon/{month_name}-{day}-{date.year}.html"
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            for url in url_patterns:
                try:
                    self.logger.debug(f"Trying URL: {url}")
                    response = requests.get(url, headers=headers, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        devotional = self._parse_devotional_html(response.text, date)
                        if devotional:
                            devotional['source_url'] = url
                            self.logger.info(f"Successfully fetched Faith's Checkbook devotional for {date.strftime('%B %d')}")
                            return devotional
                    
                except requests.RequestException as e:
                    self.logger.debug(f"Failed to fetch from {url}: {e}")
                    continue
            
            # If web scraping fails, try to get from local backup or create a fallback
            return self._get_fallback_devotional(date)
            
        except Exception as e:
            self.logger.error(f"Error fetching Faith's Checkbook devotional: {e}")
            return self._get_fallback_devotional(date)

    def _parse_devotional_html(self, html_content: str, date: datetime) -> Optional[Dict[str, Any]]:
        """Parse HTML content to extract devotional information."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for devotional content in various common HTML structures
            devotional_text = None
            scripture_reference = None
            title = None
            
            # Try to find the main content area
            content_selectors = [
                '.devotional-content',
                '.article-content', 
                '.content',
                '.main-content',
                'article',
                '.devotional-text'
            ]
            
            content_area = None
            for selector in content_selectors:
                content_area = soup.select_one(selector)
                if content_area:
                    break
            
            if not content_area:
                # Fallback to finding largest text block
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content_area = max(paragraphs, key=lambda p: len(p.get_text()))
            
            if content_area:
                # Extract title
                title_elem = content_area.find(['h1', 'h2', 'h3']) or soup.find(['h1', 'h2', 'h3'])
                if title_elem:
                    title = title_elem.get_text().strip()
                
                # Extract scripture reference (usually in italics, quotes, or citation format)
                scripture_patterns = [
                    r'([1-3]?\s*[A-Za-z]+\s+\d+:\d+(?:-\d+)?)',  # Basic verse reference
                    r'(\b[A-Za-z]+\s+\d+:\d+\b)',  # Simple book chapter:verse
                ]
                
                text_content = content_area.get_text()
                for pattern in scripture_patterns:
                    match = re.search(pattern, text_content)
                    if match:
                        scripture_reference = match.group(1).strip()
                        break
                
                # Extract devotional text (remove HTML tags but keep formatting)
                devotional_text = self._clean_devotional_text(content_area.get_text())
            
            if devotional_text and len(devotional_text.strip()) > 50:  # Minimum meaningful content
                return {
                    'date': date.strftime('%B %d'),
                    'month': date.month,
                    'day': date.day,
                    'title': title or f"Faith's Checkbook - {date.strftime('%B %d')}",
                    'scripture_reference': scripture_reference or '',
                    'devotional_text': devotional_text,
                    'author': 'Charles Spurgeon',
                    'source': "Faith's Checkbook",
                    'fetched_date': datetime.now().isoformat()
                }
            
        except Exception as e:
            self.logger.error(f"Error parsing devotional HTML: {e}")
        
        return None

    def _clean_devotional_text(self, text: str) -> str:
        """Clean and format devotional text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common web page artifacts
        artifacts = [
            r'Share this devotional.*?$',
            r'Subscribe to.*?$',
            r'Follow us.*?$',
            r'Copyright.*?$',
            r'All rights reserved.*?$'
        ]
        
        for artifact in artifacts:
            text = re.sub(artifact, '', text, flags=re.IGNORECASE)
        
        # Remove date references and Faith's Checkbook titles
        text = re.sub(r'^[A-Z][a-z]+ \d{1,2}[a-z]{0,2}[,\s]*', '', text)
        text = re.sub(r'^\d{1,2}[a-z]{0,2} [A-Z][a-z]+[,\s]*', '', text)
        text = re.sub(r'[A-Z][a-z]+ \d{1,2}[a-z]{0,2}[,\s]*\d{4}', '', text)
        text = re.sub(r'Faith\'s Checkbook\s*-\s*[A-Z][a-z]+\s*\d{1,2}[a-z]{0,2}[,\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Faith\'s Checkbook[,\s]*', '', text, flags=re.IGNORECASE)
        
        # Remove pagination references
        text = re.sub(r'pages?\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'page\s+\d+', '', text, flags=re.IGNORECASE)
        
        # Limit length to reasonable devotional size
        if len(text) > 2000:  # Reasonable limit for daily devotional
            text = text[:1950] + "..."
        
        return text.strip()

    def _get_fallback_devotional(self, date: datetime) -> Dict[str, Any]:
        """Provide a fallback devotional when web sources fail."""
        # Simple fallback with basic structure
        fallback_devotions = {
            (1, 1): {
                'scripture_reference': 'Psalm 23:1',
                'devotional_text': 'The Lord is my shepherd; I shall not want. In this new year, let us remember that our Good Shepherd provides for all our needs. Trust in His guidance and provision each day.'
            },
            (7, 2): {  # Example for July 2
                'scripture_reference': 'Psalm 127:2',
                'devotional_text': 'It is vain for you to rise up early, to sit up late, to eat the bread of sorrows: for so he giveth his beloved sleep. God desires that we find rest in Him, not in our anxious labors.'
            }
        }
        
        fallback = fallback_devotions.get((date.month, date.day), {
            'scripture_reference': 'Philippians 4:19',
            'devotional_text': 'And my God shall supply all your need according to his riches in glory by Christ Jesus. Trust in God\'s faithful provision for this day.'
        })
        
        return {
            'date': date.strftime('%B %d'),
            'month': date.month,
            'day': date.day,
            'title': f"Faith's Checkbook - {date.strftime('%B %d')}",
            'scripture_reference': fallback['scripture_reference'],
            'devotional_text': fallback['devotional_text'],
            'author': 'Charles Spurgeon',
            'source': "Faith's Checkbook (Fallback)",
            'fetched_date': datetime.now().isoformat(),
            'is_fallback': True
        }

    def get_devotional_stats(self) -> Dict[str, Any]:
        """Get statistics about cached devotionals."""
        total_cached = len(self.devotional_cache)
        sources_count = {}
        
        for devotional in self.devotional_cache.values():
            source = devotional.get('source', 'Unknown')
            sources_count[source] = sources_count.get(source, 0) + 1
        
        # Get current rotation info
        now = datetime.now()
        minutes_since_midnight = now.hour * 60 + now.minute
        current_slot = (minutes_since_midnight // 15) % 96
        next_rotation = self._get_next_rotation_time(now, 15)
        
        return {
            'total_cached': total_cached,
            'sources': sources_count,
            'cache_enabled': self.devotional_cache_enabled,
            'available_sources': list(self.sources.keys()),
            'rotation': {
                'enabled': True,
                'interval_minutes': 15,
                'current_slot': current_slot,
                'total_slots': 96,
                'next_change_at': next_rotation.strftime('%H:%M'),
                'slots_per_day': 96
            }
        }

    def clear_cache(self, older_than_days: int = 0):
        """Clear devotional cache."""
        if older_than_days > 0:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            keys_to_remove = []
            
            for key, devotional in self.devotional_cache.items():
                cached_date = datetime.fromisoformat(devotional.get('cached_date', '1970-01-01'))
                if cached_date < cutoff_date:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.devotional_cache[key]
            
            self.logger.info(f"Cleared {len(keys_to_remove)} old devotionals from cache")
        else:
            self.devotional_cache.clear()
            self.logger.info("Cleared all devotionals from cache")
        
        self._save_devotional_cache()

if __name__ == "__main__":
    # Test the devotional manager
    logging.basicConfig(level=logging.INFO)
    
    manager = DevotionalManager()
    
    # Get today's devotional
    today_devotional = manager.get_today_devotional()
    if today_devotional:
        print(f"Today's Devotional ({today_devotional['date']}):")
        print(f"Scripture: {today_devotional['scripture_reference']}")
        print(f"Text: {today_devotional['devotional_text'][:200]}...")
    else:
        print("Could not fetch today's devotional")
    
    # Show stats
    stats = manager.get_devotional_stats()
    print(f"\nDevotional Stats: {stats}")