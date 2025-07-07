"""
Generates images for Bible verses with backgrounds and typography.
"""

import os
import random
import logging
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import textwrap
from datetime import datetime

class ImageGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.width = int(os.getenv('DISPLAY_WIDTH', '1872'))
        self.height = int(os.getenv('DISPLAY_HEIGHT', '1404'))
        
        # Enhanced font management
        self.available_fonts = {}
        self.current_font_name = 'default'
        
        # Font sizes (configurable)
        self.title_size = int(os.getenv('TITLE_FONT_SIZE', '48'))
        self.verse_size = int(os.getenv('VERSE_FONT_SIZE', '80'))  # Larger default
        self.reference_size = int(os.getenv('REFERENCE_FONT_SIZE', '84'))  # Make reference larger and more prominent
        
        # Background cycling settings
        self.background_cycling_enabled = False
        self.background_cycling_interval = 30  # minutes
        self.last_background_cycle = datetime.now()
        
        self._discover_fonts()
        
        # Load fonts
        self._load_fonts()
        
        # Load background images
        self._load_backgrounds()
        
        # Current background index for cycling
        self.current_background_index = 0
        self.last_background_index = 0  # Track background changes
        
        # Reference positioning settings (configurable via web interface)
        self.reference_position = 'center-top'  # Always keep at center-top
        self.reference_x_offset = 0  # Custom X offset from calculated position
        self.reference_y_offset = 30  # Push reference down 30 pixels from top (was 20)
        self.reference_margin = 20   # Margin from edges
    
    def _get_font(self, size: int):
        """Get a font at the specified size."""
        try:
            # Try system DejaVu fonts first
            system_dejavu_path = Path('/usr/share/fonts/truetype/dejavu')
            if system_dejavu_path.exists():
                return ImageFont.truetype(str(system_dejavu_path / 'DejaVuSans.ttf'), size)
            else:
                # Fallback to local fonts
                font_dir = Path('data/fonts')
                return ImageFont.truetype(str(font_dir / 'DejaVuSans.ttf'), size)
        except Exception as e:
            self.logger.warning(f"Failed to load font at size {size}: {e}")
            # Return default font
            try:
                return ImageFont.load_default()
            except:
                return None
    
    def _load_fonts(self):
        """Load fonts for text rendering."""
        # Try system fonts first
        system_dejavu_path = Path('/usr/share/fonts/truetype/dejavu')
        font_dir = Path('data/fonts')
        
        try:
            # Try system DejaVu fonts first
            if system_dejavu_path.exists():
                self.title_font = ImageFont.truetype(str(system_dejavu_path / 'DejaVuSans-Bold.ttf'), self.title_size)
                self.verse_font = ImageFont.truetype(str(system_dejavu_path / 'DejaVuSans.ttf'), self.verse_size)
                self.reference_font = ImageFont.truetype(str(system_dejavu_path / 'DejaVuSans-Bold.ttf'), self.reference_size)
                self.logger.info("System DejaVu fonts loaded successfully")
            else:
                # Fallback to local fonts
                self.title_font = ImageFont.truetype(str(font_dir / 'DejaVuSans-Bold.ttf'), self.title_size)
                self.verse_font = ImageFont.truetype(str(font_dir / 'DejaVuSans.ttf'), self.verse_size)
                self.reference_font = ImageFont.truetype(str(font_dir / 'DejaVuSans-Bold.ttf'), self.reference_size)
                self.logger.info("Local fonts loaded successfully")
        except Exception as e:
            self.logger.warning(f"Failed to load DejaVu fonts: {e}")
            # Use system NimbusSans as fallback instead of default font
            try:
                nimbus_path = '/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf'
                nimbus_bold_path = '/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf'
                self.title_font = ImageFont.truetype(nimbus_bold_path, self.title_size)
                self.verse_font = ImageFont.truetype(nimbus_path, self.verse_size)
                self.reference_font = ImageFont.truetype(nimbus_bold_path, self.reference_size)
                self.logger.info("NimbusSans fallback fonts loaded")
            except:
                self.logger.error("All font loading failed - using minimal fallback")
                self.title_font = None
                self.verse_font = None
                self.reference_font = None
    
    def _discover_fonts(self):
        """Discover available fonts."""
        font_dir = Path('data/fonts')
        self.available_fonts = {'default': None}
        
        if font_dir.exists():
            for font_file in font_dir.glob('*.ttf'):
                font_name = font_file.stem
                try:
                    # Test loading the font
                    test_font = ImageFont.truetype(str(font_file), 24)
                    self.available_fonts[font_name] = str(font_file)
                    self.logger.debug(f"Found font: {font_name}")
                except Exception as e:
                    self.logger.warning(f"Could not load font {font_file}: {e}")
    
    def _load_backgrounds(self):
        """Initialize background metadata for lazy loading."""
        self.background_files = []  # Store file paths instead of loaded images
        self.background_names = []
        self.background_cache = {}  # LRU cache for loaded backgrounds
        self.max_cached_backgrounds = 3  # Limit cached backgrounds
        background_dir = Path('images')
        
        if not background_dir.exists():
            self.logger.warning(f"Background directory {background_dir} does not exist")
            self.background_files.append(None)  # Marker for default background
            self.background_names.append("Default Background")
            return
        
        # Get all PNG files in the images directory, sorted by filename
        background_files = sorted(background_dir.glob('*.png'))
        
        if not background_files:
            self.logger.warning("No PNG background files found in images directory")
            self.background_files.append(None)  # Marker for default background
            self.background_names.append("Default Background")
            return
        
        for bg_path in background_files:
            try:
                # Just store the path and extract name, don't load image yet
                self.background_files.append(bg_path)
                
                # Extract readable name from filename (remove number prefix and extension)
                name = bg_path.stem
                if '_' in name and name.split('_')[0].isdigit():
                    # Remove number prefix (e.g., "01_Golden_Cross_Traditional" -> "Golden Cross Traditional")
                    name = '_'.join(name.split('_')[1:]).replace('_', ' ')
                else:
                    name = name.replace('_', ' ')
                
                self.background_names.append(name)
                self.logger.debug(f"Found background: {bg_path.name} as '{name}'")
                
            except Exception as e:
                self.logger.warning(f"Failed to read background {bg_path.name}: {e}")
        
        if not self.background_files:
            # Create a marker for default background if none found
            self.background_files.append(None)
            self.background_names.append("Default Background")
            self.logger.info("Using default background")
        else:
            self.logger.info(f"Found {len(self.background_files)} background images (lazy loading enabled)")
    
    def _create_default_background(self) -> Image.Image:
        """Create a simple default background."""
        bg = Image.new('L', (self.width, self.height), 255)  # White background
        draw = ImageDraw.Draw(bg)
        
        # Add a simple border
        border_width = 20
        draw.rectangle([
            border_width, border_width,
            self.width - border_width, self.height - border_width
        ], outline=128, width=3)
        
        return bg
    
    def _get_background(self, index: int) -> Image.Image:
        """Lazy load background image with LRU cache."""
        if index < 0 or index >= len(self.background_files):
            self.logger.warning(f"Invalid background index {index}, using default")
            return self._create_default_background()
        
        # Check if already cached
        if index in self.background_cache:
            return self.background_cache[index].copy()
        
        # Load background
        bg_file = self.background_files[index]
        
        if bg_file is None:
            # Default background
            background = self._create_default_background()
        else:
            try:
                bg_image = Image.open(bg_file)
                # Resize to display dimensions
                bg_image = bg_image.resize((self.width, self.height), Image.Resampling.LANCZOS)
                # Convert to grayscale for e-ink
                background = bg_image.convert('L')
                self.logger.debug(f"Lazy loaded background: {bg_file.name}")
            except Exception as e:
                self.logger.warning(f"Failed to load background {bg_file}: {e}")
                background = self._create_default_background()
        
        # Cache management - remove oldest if cache is full
        if len(self.background_cache) >= self.max_cached_backgrounds:
            # Remove the first (oldest) cached background
            oldest_key = next(iter(self.background_cache))
            del self.background_cache[oldest_key]
            self.logger.debug(f"Removed cached background {oldest_key} (cache full)")
        
        # Cache the new background
        self.background_cache[index] = background
        return background.copy()
    
    def create_verse_image(self, verse_data: Dict) -> Image.Image:
        """Create an image for a Bible verse."""
        # Track background changes for display refresh optimization
        self.last_background_index = self.current_background_index
        
        # Get current background using lazy loading
        try:
            background = self._get_background(self.current_background_index)
        except Exception as e:
            self.logger.error(f"Error loading background: {e}")
            background = self._create_default_background()
        
        # Create a fresh copy to avoid artifacts from previous renders
        background = background.copy()
        draw = ImageDraw.Draw(background)
        
        # Define text areas
        margin = 80
        content_width = self.width - (2 * margin)
        
        # Check for different verse types
        is_summary = verse_data.get('is_summary', False)
        is_date_event = verse_data.get('is_date_event', False)
        is_parallel = verse_data.get('parallel_mode', False)
        is_devotional = verse_data.get('is_devotional', False)
        
        if is_devotional:
            # Devotional mode with rotation info
            self._draw_devotional(draw, verse_data, margin, content_width)
        elif is_date_event:
            self._draw_date_event(draw, verse_data, margin, content_width)
        elif is_parallel and is_summary:
            # Special case: book summary in parallel mode - show single summary spanning both columns
            self._draw_book_summary(draw, verse_data, margin, content_width)
        elif is_parallel:
            # Regular parallel mode - split verse translations
            self._draw_parallel_verse(draw, verse_data, margin, content_width)
        elif is_summary:
            # Regular summary mode 
            self._draw_book_summary(draw, verse_data, margin, content_width)
        else:
            # Regular single verse mode
            self._draw_verse(draw, verse_data, margin, content_width)
        
        # Apply mirroring directly here if needed
        mirror_setting = os.getenv('DISPLAY_MIRROR', 'false').lower()
        if mirror_setting == 'true':
            # Apply both horizontal and vertical flip for this display
            background = background.transpose(Image.FLIP_LEFT_RIGHT)
            background = background.transpose(Image.FLIP_TOP_BOTTOM)
        
        return background
    
    def _draw_verse(self, draw: ImageDraw.Draw, verse_data: Dict, margin: int, content_width: int):
        """Draw a regular Bible verse."""
        verse_text = verse_data['text']
        
        # Auto-scale font size to fit the verse
        optimal_font = self._get_optimal_font_size(verse_text, content_width, margin)
        
        # Calculate vertical centering
        wrapped_text = self._wrap_text(verse_text, content_width, optimal_font)
        total_text_height = len(wrapped_text) * (optimal_font.size + 20) - 20  # Remove extra spacing from last line
        
        # Calculate reference position and reserve space accordingly
        ref_bbox = draw.textbbox((0, 0), verse_data.get('reference', 'Unknown'), font=self.reference_font) if self.reference_font else (0, 0, 0, 100)
        ref_height = ref_bbox[3] - ref_bbox[1]
        
        # Get margin based on decorative border presence
        has_decorative_border = self.current_background_index > 0
        base_margin = self.reference_margin if hasattr(self, 'reference_margin') else 20
        if has_decorative_border:
            base_margin = max(base_margin, 80)
        
        # Center verse vertically with minimal spacing from reference
        # Calculate actual reference Y position to ensure proper spacing (match _add_verse_reference_display logic)
        ref_y = base_margin + self.reference_y_offset  # Match the reference positioning exactly
        min_gap = 40  # Minimum gap between reference and verse text
        reference_bottom = ref_y + ref_height + min_gap
        
        # Calculate available space for verse centering
        available_height = self.height - reference_bottom - margin
        
        # Center verse vertically in the remaining space
        y_position = reference_bottom + (available_height - total_text_height) // 2
        
        # Ensure minimum top margin
        y_position = max(margin, y_position)
        
        # Draw verse text (wrapped and centered)
        for line in wrapped_text:
            if optimal_font:
                line_bbox = draw.textbbox((0, 0), line, font=optimal_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (self.width - line_width) // 2
                draw.text((line_x, y_position), line, fill=0, font=optimal_font)
                y_position += line_bbox[3] - line_bbox[1] + 20
        
        # Add verse reference in bottom-right corner
        self._add_verse_reference_display(draw, verse_data)
    
    def _draw_book_summary(self, draw: ImageDraw.Draw, verse_data: Dict, margin: int, content_width: int):
        """Draw a book summary with page cycling for long text."""
        
        # Check if we need pagination and get current page
        pages = self._paginate_book_summary_text(verse_data['text'], content_width, margin)
        
        if not pages or len(pages) == 1:
            # Single page or pagination failed - use original behavior
            self._draw_book_summary_single_page(draw, verse_data, margin, content_width)
            return
        
        # Calculate current page based on time rotation (same as devotionals)
        # Use 15-second rotation interval for pages
        from datetime import datetime
        now = datetime.now()
        page_rotation_seconds = 15  # Change page every 15 seconds
        seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
        page_slot = (seconds_since_midnight // page_rotation_seconds) % len(pages)
        current_page = page_slot + 1  # Pages are 1-indexed
        
        # Update verse_data with page information
        verse_data['current_page'] = current_page
        verse_data['total_pages'] = len(pages)
        
        # Get current page content
        page_content = pages[page_slot]
        
        # Draw the current page
        self._draw_book_summary_page(draw, verse_data, page_content, margin, content_width)
        
        # Add verse reference display (shows current time for summaries)
        self._add_verse_reference_display(draw, verse_data)

    def _draw_book_summary_single_page(self, draw: ImageDraw.Draw, verse_data: Dict, margin: int, content_width: int):
        """Draw a book summary that fits on a single page (original implementation)."""
        
        # Get book name for the title
        book_name = verse_data.get('book', 'Unknown Book')
        
        # Calculate reference position and reserve space (same logic as _draw_verse)
        ref_bbox = draw.textbbox((0, 0), verse_data.get('reference', 'Unknown'), font=self.reference_font) if self.reference_font else (0, 0, 0, 100)
        ref_height = ref_bbox[3] - ref_bbox[1]
        
        # Get margin based on decorative border presence
        has_decorative_border = self.current_background_index > 0
        base_margin = self.reference_margin if hasattr(self, 'reference_margin') else 20
        if has_decorative_border:
            base_margin = max(base_margin, 80)
        
        # Calculate actual reference Y position to ensure proper spacing
        ref_y = base_margin + self.reference_y_offset  # Match the reference positioning exactly
        min_gap = 40  # Minimum gap between reference and content
        reference_bottom = ref_y + ref_height + min_gap
        
        # Draw book title
        book_title = f"Book of {book_name}"
        if self.title_font:
            title_bbox = draw.textbbox((0, 0), book_title, font=self.title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            title_x = (self.width - title_width) // 2
            title_y = reference_bottom
            draw.text((title_x, title_y), book_title, fill=0, font=self.title_font)
            
            # Update starting position for summary text
            content_start_y = title_y + title_height + 30  # 30px gap after title
        else:
            content_start_y = reference_bottom
        
        # Prepare summary text
        summary_text = verse_data['text']
        wrapped_text = self._wrap_text(summary_text, content_width, self.verse_font)
        
        # Calculate total text height for centering
        total_text_height = len(wrapped_text) * (self.verse_font.size + 25) - 25 if wrapped_text else 0
        
        # Calculate available space for centering the summary
        available_height = self.height - content_start_y - margin
        
        # Center the summary text vertically in remaining space
        y_position = content_start_y + (available_height - total_text_height) // 2
        y_position = max(content_start_y, y_position)  # Don't go above content start
        
        # Draw summary text (wrapped and centered)
        for line in wrapped_text:
            if self.verse_font:
                line_bbox = draw.textbbox((0, 0), line, font=self.verse_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (self.width - line_width) // 2
                draw.text((line_x, y_position), line, fill=0, font=self.verse_font)
                y_position += line_bbox[3] - line_bbox[1] + 25

    def _paginate_book_summary_text(self, text: str, content_width: int, margin: int) -> List[str]:
        """Split book summary text into pages that fit the display (similar to devotionals)."""
        # Use a reasonable font size for pagination calculation
        test_font = self._get_font(self.verse_size)
        
        # Calculate available space for content
        ref_bbox = (0, 0, 0, 100)  # Approximate reference height
        ref_height = ref_bbox[3] - ref_bbox[1]
        has_decorative_border = self.current_background_index > 0
        base_margin = self.reference_margin if hasattr(self, 'reference_margin') else 20
        if has_decorative_border:
            base_margin = max(base_margin, 80)
        
        ref_y = base_margin + self.reference_y_offset
        min_gap = 40
        reference_bottom = ref_y + ref_height + min_gap
        title_height = 60  # Approximate title height for "Book of [Name]"
        available_height = self.height - reference_bottom - title_height - margin - 60  # Reserve space for page info
        
        # Calculate max lines per page
        line_height = test_font.size + 25 if test_font else 30  # Match book summary line spacing
        max_lines_per_page = max(3, available_height // line_height)  # Minimum 3 lines per page
        
        # Wrap text and split into pages
        wrapped_lines = self._wrap_text(text, content_width, test_font)
        
        # If text fits on one page, return single page
        if len(wrapped_lines) <= max_lines_per_page:
            return [text]
        
        # Split into pages
        pages = []
        for i in range(0, len(wrapped_lines), max_lines_per_page):
            page_lines = wrapped_lines[i:i + max_lines_per_page]
            pages.append(' '.join(page_lines))
        
        return pages

    def _draw_book_summary_page(self, draw: ImageDraw.Draw, verse_data: Dict, page_content: str, margin: int, content_width: int):
        """Draw a single page of book summary content."""
        
        # Get book name for the title
        book_name = verse_data.get('book', 'Unknown Book')
        
        # Calculate reference position and reserve space
        ref_bbox = draw.textbbox((0, 0), verse_data.get('reference', 'Unknown'), font=self.reference_font) if self.reference_font else (0, 0, 0, 100)
        ref_height = ref_bbox[3] - ref_bbox[1]
        
        # Get margin based on decorative border presence
        has_decorative_border = self.current_background_index > 0
        base_margin = self.reference_margin if hasattr(self, 'reference_margin') else 20
        if has_decorative_border:
            base_margin = max(base_margin, 80)
        
        # Calculate actual reference Y position
        ref_y = base_margin + self.reference_y_offset
        min_gap = 40
        reference_bottom = ref_y + ref_height + min_gap
        
        # Draw book title
        book_title = f"Book of {book_name}"
        if self.title_font:
            title_bbox = draw.textbbox((0, 0), book_title, font=self.title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            title_x = (self.width - title_width) // 2
            title_y = reference_bottom
            draw.text((title_x, title_y), book_title, fill=0, font=self.title_font)
            
            content_start_y = title_y + title_height + 30
        else:
            content_start_y = reference_bottom
        
        # Draw page indicator if multiple pages
        if verse_data.get('total_pages', 1) > 1:
            page_info = f"Page {verse_data.get('current_page', 1)} of {verse_data.get('total_pages', 1)}"
            if self.reference_font:
                page_info_bbox = draw.textbbox((0, 0), page_info, font=self.reference_font)
                page_info_width = page_info_bbox[2] - page_info_bbox[0]
                page_info_x = (self.width - page_info_width) // 2
                page_info_y = content_start_y
                draw.text((page_info_x, page_info_y), page_info, fill=0, font=self.reference_font)
                content_start_y += page_info_bbox[3] - page_info_bbox[1] + 20
        
        # Use consistent font size for all pages
        page_font = self._get_font(self.verse_size)
        
        # Wrap page content
        wrapped_text = self._wrap_text(page_content, content_width, page_font)
        
        # Draw page text
        y_position = content_start_y
        for line in wrapped_text:
            if page_font:
                line_bbox = draw.textbbox((0, 0), line, font=page_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (self.width - line_width) // 2
                draw.text((line_x, y_position), line, fill=0, font=page_font)
                y_position += page_font.size + 25  # Match book summary line spacing
    
    def _get_optimal_font_size(self, text: str, content_width: int, margin: int) -> ImageFont.ImageFont:
        """Get optimal font size that fits the text within the display bounds."""
        max_font_size = self.verse_size
        min_font_size = 24
        available_height = self.height - (2 * margin) - 120  # Reserve space for bottom-right reference
        
        # Start with desired size and scale down if needed
        for font_size in range(max_font_size, min_font_size - 1, -2):
            try:
                # Use system DejaVu fonts
                system_dejavu_path = Path('/usr/share/fonts/truetype/dejavu')
                if system_dejavu_path.exists():
                    test_font = ImageFont.truetype(str(system_dejavu_path / 'DejaVuSans.ttf'), font_size)
                elif self.current_font_name != 'default' and self.available_fonts[self.current_font_name]:
                    test_font = ImageFont.truetype(self.available_fonts[self.current_font_name], font_size)
                else:
                    test_font = ImageFont.truetype(str(Path('data/fonts/DejaVuSans.ttf')), font_size)
                
                # Test if text fits
                wrapped_text = self._wrap_text(text, content_width, test_font)
                total_height = len(wrapped_text) * (font_size + 20)
                
                if total_height <= available_height:
                    return test_font
                    
            except Exception:
                # Fallback to default font
                try:
                    test_font = ImageFont.load_default()
                    wrapped_text = self._wrap_text(text, content_width, test_font)
                    return test_font
                except:
                    continue
        
        # If all else fails, use minimum size
        try:
            # Use system DejaVu fonts for fallback
            system_dejavu_path = Path('/usr/share/fonts/truetype/dejavu')
            if system_dejavu_path.exists():
                return ImageFont.truetype(str(system_dejavu_path / 'DejaVuSans.ttf'), min_font_size)
            elif self.current_font_name != 'default' and self.available_fonts[self.current_font_name]:
                return ImageFont.truetype(self.available_fonts[self.current_font_name], min_font_size)
            else:
                return ImageFont.truetype(str(Path('data/fonts/DejaVuSans.ttf')), min_font_size)
        except:
            return ImageFont.load_default()

    def _get_optimal_font_size_parallel(self, primary_text: str, secondary_text: str, column_width: int, margin: int) -> ImageFont.ImageFont:
        """Get optimal font size for parallel translations."""
        max_font_size = min(self.verse_size, 55)  # Even smaller max for parallel mode
        min_font_size = 18
        
        # More conservative height calculation for parallel mode
        # Account for reference, translation labels, and proper spacing
        ref_height = 100  # Estimate for reference text height
        label_height = 40   # Estimate for translation label height
        spacing_margin = 100  # Extra margin for proper spacing
        available_height = self.height - (2 * margin) - ref_height - label_height - spacing_margin
        
        # Test both texts and find size that fits both comfortably
        for font_size in range(max_font_size, min_font_size - 1, -2):
            try:
                # Use system DejaVu fonts
                system_dejavu_path = Path('/usr/share/fonts/truetype/dejavu')
                if system_dejavu_path.exists():
                    test_font = ImageFont.truetype(str(system_dejavu_path / 'DejaVuSans.ttf'), font_size)
                elif self.current_font_name != 'default' and self.available_fonts[self.current_font_name]:
                    test_font = ImageFont.truetype(self.available_fonts[self.current_font_name], font_size)
                else:
                    test_font = ImageFont.truetype(str(Path('data/fonts/DejaVuSans.ttf')), font_size)
                
                # Test both texts with more conservative line spacing
                wrapped_primary = self._wrap_text(primary_text, column_width, test_font)
                wrapped_secondary = self._wrap_text(secondary_text, column_width, test_font)
                
                max_lines = max(len(wrapped_primary), len(wrapped_secondary))
                total_height = max_lines * (font_size + 18)  # Slightly more line spacing for parallel mode
                
                # Be more conservative - only use this size if it fits comfortably
                if total_height <= available_height * 0.9:  # Use only 90% of available space for safety
                    return test_font
                    
            except Exception:
                continue
        
        # Fallback
        try:
            # Use system DejaVu fonts for fallback
            system_dejavu_path = Path('/usr/share/fonts/truetype/dejavu')
            if system_dejavu_path.exists():
                return ImageFont.truetype(str(system_dejavu_path / 'DejaVuSans.ttf'), min_font_size)
            elif self.current_font_name != 'default' and self.available_fonts[self.current_font_name]:
                return ImageFont.truetype(self.available_fonts[self.current_font_name], min_font_size)
            else:
                return ImageFont.truetype(str(Path('data/fonts/DejaVuSans.ttf')), min_font_size)
        except:
            return ImageFont.load_default()

    def _wrap_text(self, text: str, max_width: int, font: Optional[ImageFont.ImageFont]) -> list:
        """Wrap text to fit within specified width."""
        if not font:
            # Simple character-based wrapping if no font available
            chars_per_line = max_width // 10  # Rough estimate
            return textwrap.wrap(text, width=chars_per_line)
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Word is too long, break it
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _add_decorative_elements(self, draw: ImageDraw.Draw, y_position: int):
        """Add decorative elements to the image."""
        # Add a simple decorative line
        if y_position < self.height - 200:
            line_y = y_position + 40
            line_start = self.width // 4
            line_end = 3 * self.width // 4
            draw.line([(line_start, line_y), (line_end, line_y)], fill=128, width=2)
    
    def create_splash_image(self, message: str) -> Image.Image:
        """Create splash screen image."""
        # Use a simple background for splash
        image = Image.new('L', (self.width, self.height), 255)
        draw = ImageDraw.Draw(image)
        
        # Add border
        border_width = 40
        draw.rectangle([
            border_width, border_width,
            self.width - border_width, self.height - border_width
        ], outline=0, width=5)
        
        # Draw message
        margin = 100
        content_width = self.width - (2 * margin)
        
        wrapped_text = self._wrap_text(message, content_width, self.title_font)
        y_position = (self.height - len(wrapped_text) * 60) // 2
        
        for line in wrapped_text:
            if self.title_font:
                line_bbox = draw.textbbox((0, 0), line, font=self.title_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (self.width - line_width) // 2
                draw.text((line_x, y_position), line, fill=0, font=self.title_font)
                y_position += 60
        
        return image
    
    def cycle_background(self):
        """Cycle to the next background image."""
        self.current_background_index = (self.current_background_index + 1) % len(self.background_files)
        self.logger.info(f"Switched to background {self.current_background_index + 1}/{len(self.background_files)}")
    
    def background_changed_since_last_render(self) -> bool:
        """Check if background has changed since last render."""
        return self.current_background_index != self.last_background_index
    
    def get_current_background_info(self) -> Dict:
        """Get information about current background."""
        if hasattr(self, 'background_names') and self.background_names:
            current_name = self.background_names[self.current_background_index]
        else:
            current_name = f"Background {self.current_background_index + 1}"
            
        return {
            'current_index': self.current_background_index,
            'total_backgrounds': len(self.background_files),
            'current_name': current_name
        }
    
    def get_available_fonts(self) -> List[str]:
        """Get list of available font names."""
        return list(self.available_fonts.keys())
    
    def get_current_font(self) -> str:
        """Get current font name."""
        return self.current_font_name
    
    def set_font(self, font_name: str):
        """Set current font."""
        if font_name in self.available_fonts:
            self.current_font_name = font_name
            self._load_fonts_with_selection()  # Reload fonts with new selection
            self.logger.info(f"Font changed to: {font_name}")
        else:
            raise ValueError(f"Font not available: {font_name}")
    
    def _load_fonts_with_selection(self):
        """Load fonts using the current font selection."""
        try:
            if self.current_font_name != 'default' and self.current_font_name in self.available_fonts and self.available_fonts[self.current_font_name]:
                font_path = self.available_fonts[self.current_font_name]
                self.title_font = ImageFont.truetype(font_path, self.title_size)
                self.verse_font = ImageFont.truetype(font_path, self.verse_size)
                self.reference_font = ImageFont.truetype(font_path, self.reference_size)
                self.logger.info(f"Loaded font: {self.current_font_name}")
            else:
                # Use default font loading
                self._load_fonts()
        except Exception as e:
            self.logger.warning(f"Failed to load selected font {self.current_font_name}: {e}")
            # Fallback to default font loading
            self._load_fonts()
    
    def set_font_temporarily(self, font_name: str):
        """Temporarily set font for preview without persisting."""
        if font_name in self.available_fonts:
            old_font = self.current_font_name
            self.current_font_name = font_name
            self._load_fonts()
            return old_font
        return None
    
    def get_available_backgrounds(self) -> List[Dict]:
        """Get available backgrounds with metadata and thumbnails."""
        bg_info = []
        for i in range(len(self.background_files)):
            if hasattr(self, 'background_names') and self.background_names and i < len(self.background_names):
                name = self.background_names[i]
            else:
                name = f"Background {i + 1}"
            
            # Generate thumbnail filename
            bg_filename = f"{i+1:02d}_{name.replace(' ', '_')}.png"
            thumb_filename = f"thumb_{bg_filename.replace('.png', '.jpg')}"
            
            bg_info.append({
                'index': i,
                'name': name,
                'thumbnail': f"/static/thumbnails/{thumb_filename}",
                'current': i == self.current_background_index
            })
        return bg_info
    
    def set_background(self, index: int):
        """Set background by index."""
        if 0 <= index < len(self.background_files):
            self.current_background_index = index
            self.logger.info(f"Background changed to index: {index}")
        else:
            raise ValueError(f"Background index out of range: {index}")
    
    def get_background_info(self) -> Dict:
        """Get detailed background information."""
        return {
            'current_index': self.current_background_index,
            'total_count': len(self.background_files),
            'backgrounds': self.get_available_backgrounds()
        }
    
    def get_current_background_info(self) -> Dict:
        """Get current background information."""
        if hasattr(self, 'background_names') and self.background_names and self.current_background_index < len(self.background_names):
            name = self.background_names[self.current_background_index]
        else:
            name = f"Background {self.current_background_index + 1}"
            
        return {
            'index': self.current_background_index,
            'name': name,
            'total': len(self.background_files)
        }
    
    def set_background_cycling(self, enabled: bool, interval_minutes: int = 30):
        """Configure background cycling."""
        self.background_cycling_enabled = enabled
        self.background_cycling_interval = interval_minutes
        if enabled:
            self.last_background_cycle = datetime.now()
            self.logger.info(f"Background cycling enabled: every {interval_minutes} minutes")
        else:
            self.logger.info("Background cycling disabled")
    
    def check_background_cycling(self):
        """Check if it's time to cycle background and do it if needed."""
        if not self.background_cycling_enabled:
            return False
            
        now = datetime.now()
        time_diff = (now - self.last_background_cycle).total_seconds() / 60  # minutes
        
        if time_diff >= self.background_cycling_interval:
            self.cycle_background()
            self.last_background_cycle = now
            self.logger.info(f"Auto-cycled background to {self.current_background_index + 1}")
            return True
        
        return False
    
    def get_cycling_settings(self) -> Dict:
        """Get current background cycling settings."""
        return {
            'enabled': self.background_cycling_enabled,
            'interval_minutes': self.background_cycling_interval,
            'next_cycle_in_minutes': max(0, self.background_cycling_interval - 
                                       int((datetime.now() - self.last_background_cycle).total_seconds() / 60))
        }
    
    def get_available_fonts(self) -> List[Dict]:
        """Get available fonts with metadata."""
        fonts = []
        for name, path in self.available_fonts.items():
            display_name = name.replace('_', ' ').replace('-', ' ').title() if name != 'default' else 'Default Font'
            fonts.append({
                'name': name,
                'display_name': display_name,
                'path': path,
                'current': name == self.current_font_name
            })
        return fonts
    
    def get_current_font(self) -> str:
        """Get current font name."""
        return self.current_font_name
    
    def set_font_sizes(self, title_size: int = None, verse_size: int = None, reference_size: int = None):
        """Set font sizes."""
        if title_size is not None:
            self.title_size = max(12, min(72, title_size))  # Clamp between 12-72
        if verse_size is not None:
            self.verse_size = max(12, min(120, verse_size))  # Clamp between 12-120 for larger text
        if reference_size is not None:
            self.reference_size = max(12, min(120, reference_size))  # Clamp between 12-120 for larger, more prominent reference
        
        # Reload fonts with new sizes
        self._load_fonts()
        self.logger.info(f"Font sizes updated - Verse: {self.verse_size}, Reference: {self.reference_size}")
    
    def get_font_sizes(self) -> Dict[str, int]:
        """Get current font sizes."""
        return {
            'title_size': self.title_size,
            'verse_size': self.verse_size,
            'reference_size': self.reference_size
        }
    
    def randomize_background(self):
        """Set random background."""
        if len(self.background_files) > 1:
            # Ensure we don't select the same background
            old_index = self.current_background_index
            while self.current_background_index == old_index:
                self.current_background_index = random.randint(0, len(self.background_files) - 1)
            self.logger.info(f"Background randomized to index: {self.current_background_index}")
    
    def set_reference_position(self, position: str, x_offset: int = 0, y_offset: int = 0, margin: int = None):
        """Set verse reference position and offsets."""
        valid_positions = ['bottom-right', 'bottom-left', 'top-right', 'top-left', 'center-top', 'center-bottom', 'top-center-right', 'custom']
        if position in valid_positions:
            self.reference_position = position
            self.reference_x_offset = x_offset
            self.reference_y_offset = y_offset
            if margin is not None:
                self.reference_margin = margin
            self.logger.info(f"Reference position set to: {position} with offsets ({x_offset}, {y_offset})")
        else:
            raise ValueError(f"Invalid position. Must be one of: {valid_positions}")
    
    def get_reference_position_info(self) -> Dict:
        """Get current reference position settings."""
        return {
            'position': self.reference_position,
            'x_offset': self.reference_x_offset,
            'y_offset': self.reference_y_offset,
            'margin': self.reference_margin,
            'available_positions': ['bottom-right', 'bottom-left', 'top-right', 'top-left', 'center-top', 'center-bottom', 'top-center-right', 'custom']
        }
    
    def get_font_info(self) -> Dict:
        """Get detailed font information."""
        return {
            'current_font': self.current_font_name,
            'available_fonts': [
                {
                    'name': name,
                    'path': path,
                    'current': name == self.current_font_name
                }
                for name, path in self.available_fonts.items()
            ]
        }
    
    def _draw_date_event(self, draw: ImageDraw.Draw, verse_data: Dict, margin: int, content_width: int):
        """Draw a date-based biblical event."""
        y_position = margin
        
        # Draw event name at top
        event_name = verse_data.get('event_name', 'Biblical Event')
        if self.title_font:
            title_bbox = draw.textbbox((0, 0), event_name, font=self.title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.width - title_width) // 2
            draw.text((title_x, y_position), event_name, fill=0, font=self.title_font)
            y_position += title_bbox[3] - title_bbox[1] + 40
        
        # Draw date match type indicator
        match_type = verse_data.get('date_match', 'exact')
        match_text = {
            'exact': f"Today - {datetime.now().strftime('%B %d')}",
            'week': f"This Week - {datetime.now().strftime('%B %d')}",
            'month': f"This Month - {datetime.now().strftime('%B')}",
            'season': f"This Season - {datetime.now().strftime('%B')}",
            'fallback': f"Daily Blessing - {datetime.now().strftime('%B %d')}"
        }.get(match_type, "Today")
        
        if self.reference_font:
            ref_bbox = draw.textbbox((0, 0), match_text, font=self.reference_font)
            ref_width = ref_bbox[2] - ref_bbox[0]
            ref_x = (self.width - ref_width) // 2
            draw.text((ref_x, y_position), match_text, fill=64, font=self.reference_font)
            y_position += ref_bbox[3] - ref_bbox[1] + 30
        
        # Draw reference
        reference = verse_data['reference']
        if self.reference_font:
            ref_bbox = draw.textbbox((0, 0), reference, font=self.reference_font)
            ref_width = ref_bbox[2] - ref_bbox[0]
            ref_x = (self.width - ref_width) // 2
            draw.text((ref_x, y_position), reference, fill=0, font=self.reference_font)
            y_position += ref_bbox[3] - ref_bbox[1] + 40
        
        # Draw verse text
        verse_text = verse_data['text']
        wrapped_text = self._wrap_text(verse_text, content_width, self.verse_font)
        
        for line in wrapped_text:
            if self.verse_font:
                line_bbox = draw.textbbox((0, 0), line, font=self.verse_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (self.width - line_width) // 2
                draw.text((line_x, y_position), line, fill=0, font=self.verse_font)
                y_position += line_bbox[3] - line_bbox[1] + 20
        
        # Draw event description if space allows
        if y_position < self.height - 200:
            y_position += 40
            description = verse_data.get('event_description', '')
            if description:
                wrapped_desc = self._wrap_text(description, content_width, self.reference_font)
                for line in wrapped_desc[:2]:  # Max 2 lines for description
                    if self.reference_font:
                        line_bbox = draw.textbbox((0, 0), line, font=self.reference_font)
                        line_width = line_bbox[2] - line_bbox[0]
                        line_x = (self.width - line_width) // 2
                        draw.text((line_x, y_position), line, fill=96, font=self.reference_font)
                        y_position += line_bbox[3] - line_bbox[1] + 15
        
        # Add verse reference in bottom-right corner
        self._add_verse_reference_display(draw, verse_data)
    
    def _draw_devotional(self, draw: ImageDraw.Draw, verse_data: Dict, margin: int, content_width: int):
        """Draw devotional content with pagination support."""
        # Check if we need pagination and get current page
        pages = self._paginate_devotional_text(verse_data['text'], content_width, margin)
        
        if not pages or len(pages) == 1:
            # Single page or pagination failed - use original behavior
            self._draw_devotional_single_page(draw, verse_data, margin, content_width)
            return
        
        # Calculate current page based on time rotation
        # Use a different rotation interval for pages (e.g., every 10 seconds)
        from datetime import datetime
        now = datetime.now()
        page_rotation_seconds = 10  # Change page every 10 seconds
        seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
        page_slot = (seconds_since_midnight // page_rotation_seconds) % len(pages)
        current_page = page_slot + 1  # Pages are 1-indexed
        
        # Update verse_data with page information
        verse_data['current_page'] = current_page
        verse_data['total_pages'] = len(pages)
        
        # Get current page content
        page_content = pages[page_slot]
        
        # Draw the current page
        self._draw_devotional_page(draw, verse_data, page_content, margin, content_width)
        
        # Add verse reference display (shows current time for devotionals)
        self._add_verse_reference_display(draw, verse_data)

    def _draw_devotional_single_page(self, draw: ImageDraw.Draw, verse_data: Dict, margin: int, content_width: int):
        """Draw devotional content on a single page."""
        # Calculate reference position and reserve space accordingly
        ref_text = verse_data.get('reference', 'Unknown')
        ref_bbox = draw.textbbox((0, 0), ref_text, font=self.reference_font) if self.reference_font else (0, 0, 0, 100)
        ref_height = ref_bbox[3] - ref_bbox[1]
        
        # Get margin based on decorative border presence
        has_decorative_border = self.current_background_index > 0
        base_margin = self.reference_margin if hasattr(self, 'reference_margin') else 20
        if has_decorative_border:
            base_margin = max(base_margin, 80)
        
        # Calculate actual reference Y position to ensure proper spacing
        ref_y = base_margin + self.reference_y_offset
        min_gap = 40
        reference_bottom = ref_y + ref_height + min_gap
        
        # Draw devotional title
        devotional_title = verse_data.get('devotional_title', "Today's Devotional")
        content_start_y = reference_bottom
        if self.title_font:
            title_bbox = draw.textbbox((0, 0), devotional_title, font=self.title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            title_x = (self.width - title_width) // 2
            draw.text((title_x, content_start_y), devotional_title, fill=0, font=self.title_font)
            content_start_y += title_height + 30
        
        # Prepare devotional text
        devotional_text = verse_data['text']
        
        # Auto-scale font size to fit the devotional text
        available_height = self.height - content_start_y - margin - 60  # Reserve less space
        optimal_font = self._get_optimal_font_size(devotional_text, content_width, margin)
        
        # Calculate vertical centering
        wrapped_text = self._wrap_text(devotional_text, content_width, optimal_font)
        total_text_height = len(wrapped_text) * (optimal_font.size + 20) - 20
        
        # Center the devotional text vertically in remaining space
        text_start_y = content_start_y + (available_height - total_text_height) // 2
        text_start_y = max(content_start_y, text_start_y)
        
        # Draw devotional text
        y_position = text_start_y
        for line in wrapped_text:
            if optimal_font:
                line_bbox = draw.textbbox((0, 0), line, font=optimal_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (self.width - line_width) // 2
                draw.text((line_x, y_position), line, fill=0, font=optimal_font)
                y_position += line_bbox[3] - line_bbox[1] + 20

    def _paginate_devotional_text(self, text: str, content_width: int, margin: int) -> List[str]:
        """Split devotional text into pages that fit the display."""
        # Use a reasonable font size for pagination calculation
        test_font = self._get_font(self.verse_size)
        
        # Calculate available space for content
        ref_bbox = (0, 0, 0, 100)  # Approximate reference height
        ref_height = ref_bbox[3] - ref_bbox[1]
        has_decorative_border = self.current_background_index > 0
        base_margin = self.reference_margin if hasattr(self, 'reference_margin') else 20
        if has_decorative_border:
            base_margin = max(base_margin, 80)
        
        ref_y = base_margin + self.reference_y_offset
        min_gap = 40
        reference_bottom = ref_y + ref_height + min_gap
        title_height = 60  # Approximate title height
        available_height = self.height - reference_bottom - title_height - margin - 60  # Reserve space for page info
        
        # Calculate max lines per page
        line_height = test_font.size + 20 if test_font else 30
        max_lines_per_page = max(3, available_height // line_height)  # Minimum 3 lines per page
        
        # Wrap text and split into pages
        wrapped_lines = self._wrap_text(text, content_width, test_font)
        
        # If text fits on one page, return single page
        if len(wrapped_lines) <= max_lines_per_page:
            return [text]
        
        # Split into pages - use newlines to preserve line breaks
        pages = []
        for i in range(0, len(wrapped_lines), max_lines_per_page):
            page_lines = wrapped_lines[i:i + max_lines_per_page]
            pages.append('\n'.join(page_lines))
        
        return pages

    def _draw_devotional_page(self, draw: ImageDraw.Draw, verse_data: Dict, page_content: str, margin: int, content_width: int):
        """Draw a single page of devotional content."""
        # Calculate positioning
        ref_text = verse_data.get('reference', 'Unknown')
        ref_bbox = draw.textbbox((0, 0), ref_text, font=self.reference_font) if self.reference_font else (0, 0, 0, 100)
        ref_height = ref_bbox[3] - ref_bbox[1]
        
        has_decorative_border = self.current_background_index > 0
        base_margin = self.reference_margin if hasattr(self, 'reference_margin') else 20
        if has_decorative_border:
            base_margin = max(base_margin, 80)
        
        ref_y = base_margin + self.reference_y_offset
        min_gap = 40
        reference_bottom = ref_y + ref_height + min_gap
        
        # Draw devotional title
        devotional_title = verse_data.get('devotional_title', "Today's Devotional")
        content_start_y = reference_bottom
        if self.title_font:
            title_bbox = draw.textbbox((0, 0), devotional_title, font=self.title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            title_x = (self.width - title_width) // 2
            draw.text((title_x, content_start_y), devotional_title, fill=0, font=self.title_font)
            content_start_y += title_height + 30
        
        # Use consistent font size for all pages
        page_font = self._get_font(self.verse_size)
        
        # Split page content by newlines (preserve pagination line breaks)
        page_lines = page_content.split('\n')
        
        # Draw page text
        y_position = content_start_y
        for line in page_lines:
            if line.strip():  # Only draw non-empty lines
                if page_font:
                    line_bbox = draw.textbbox((0, 0), line, font=page_font)
                    line_width = line_bbox[2] - line_bbox[0]
                    line_x = (self.width - line_width) // 2
                    draw.text((line_x, y_position), line, font=page_font, fill='black')
                    y_position += page_font.size + 20
        
        # Page indicator removed per user request - devotional will cycle through pages automatically
    
    def _draw_parallel_verse(self, draw: ImageDraw.Draw, verse_data: Dict, margin: int, content_width: int):
        """Draw verse with parallel translations side by side."""
        # Split content into two columns
        column_width = (content_width - 40) // 2  # 40px gap between columns
        left_margin = margin
        right_margin = margin + column_width + 40
        
        # Get optimal font size for both texts
        primary_text = verse_data['text']
        secondary_text = verse_data.get('secondary_text', 'Translation not available')
        
        # Use smaller auto-scale for parallel mode
        optimal_font = self._get_optimal_font_size_parallel(primary_text, secondary_text, column_width, margin)
        
        # Get translation labels for bottom display
        primary_label = verse_data.get('primary_translation', 'KJV')
        secondary_label = verse_data.get('secondary_translation', 'AMP')
        
        # Calculate reference position and reserve space accordingly
        ref_text = verse_data.get('reference', 'Unknown')
        ref_bbox = draw.textbbox((0, 0), ref_text, font=self.reference_font) if self.reference_font else (0, 0, 0, 100)
        ref_height = ref_bbox[3] - ref_bbox[1]
        
        # Get margin based on decorative border presence  
        has_decorative_border = self.current_background_index > 0
        base_margin = self.reference_margin if hasattr(self, 'reference_margin') else 20
        if has_decorative_border:
            base_margin = max(base_margin, 80)
        
        # Calculate actual reference Y position to ensure proper spacing
        ref_y = base_margin + self.reference_y_offset
        min_gap = 30  # Minimum gap between verse content and reference
        
        # Calculate available space for verse content considering reference position
        if self.reference_position == 'center-top':
            # Reference is at the top, so reserve space from top
            reference_bottom = ref_y + ref_height + min_gap
            available_height = self.height - reference_bottom - margin - 80  # Extra bottom margin for translation labels
            content_start_y = reference_bottom
        else:
            # Reference is at bottom, so reserve space from bottom  
            content_start_y = margin
            available_height = self.height - content_start_y - margin - ref_height - min_gap - 80  # Reserve space for ref + labels
        
        # Calculate vertical centering for text content
        wrapped_primary = self._wrap_text(primary_text, column_width, optimal_font)
        wrapped_secondary = self._wrap_text(secondary_text, column_width, optimal_font)
        
        max_lines = max(len(wrapped_primary), len(wrapped_secondary))
        total_text_height = max_lines * (optimal_font.size + 15)
        
        # Center the text vertically in the available space
        text_start_y = content_start_y + (available_height - total_text_height) // 2
        text_start_y = max(content_start_y, text_start_y)
        
        # Ensure text doesn't extend beyond available space
        max_text_end_y = content_start_y + available_height
        if text_start_y + total_text_height > max_text_end_y:
            text_start_y = max_text_end_y - total_text_height
            text_start_y = max(content_start_y, text_start_y)
        
        # Draw primary translation (left)
        current_y = text_start_y
        for line in wrapped_primary:
            if optimal_font:
                draw.text((left_margin, current_y), line, fill=0, font=optimal_font)
                current_y += optimal_font.size + 15
        
        # Draw secondary translation (right) 
        current_y = text_start_y
        secondary_end_y = current_y
        for line in wrapped_secondary:
            if optimal_font:
                draw.text((right_margin, current_y), line, fill=0, font=optimal_font)
                current_y += optimal_font.size + 15
                secondary_end_y = current_y
        
        # Add a vertical separator line
        separator_x = margin + column_width + 20
        separator_start_y = text_start_y - 10
        separator_end_y = max(text_start_y + total_text_height, secondary_end_y) + 10
        draw.line([(separator_x, separator_start_y), (separator_x, separator_end_y)], fill=128, width=1)
        
        # Calculate translation label position with proper spacing
        verse_content_end_y = max(text_start_y + total_text_height, secondary_end_y)
        bottom_label_y = verse_content_end_y + 20  # 20px gap after verse content
        
        # Ensure labels don't conflict with reference display
        max_label_y = self.height - ref_height - min_gap - 40  # Keep labels above reference with margin
        if bottom_label_y > max_label_y:
            bottom_label_y = max_label_y
        
        # Use appropriately sized font for translation labels (larger than before)
        label_font_size = min(optimal_font.size - 4, 36) if optimal_font else 28  # Larger font for better readability
        try:
            system_dejavu_path = Path('/usr/share/fonts/truetype/dejavu')
            if system_dejavu_path.exists():
                label_font = ImageFont.truetype(str(system_dejavu_path / 'DejaVuSans.ttf'), label_font_size)
            else:
                label_font = ImageFont.truetype(str(Path('data/fonts/DejaVuSans.ttf')), label_font_size)
        except:
            label_font = optimal_font  # Fallback to verse font
        
        if label_font:
            self.logger.info(f"Drawing translation labels at y={bottom_label_y}, display height={self.height}, verse_content_end_y={verse_content_end_y}")
            
            # Left column label (primary translation) - make it very visible
            left_label = f"({primary_label})"
            left_label_bbox = draw.textbbox((0, 0), left_label, font=label_font)
            left_label_width = left_label_bbox[2] - left_label_bbox[0]
            left_label_x = left_margin + (column_width // 2) - (left_label_width // 2)
            
            # Ensure labels are visible - use black text on light background or add background
            draw.text((left_label_x, bottom_label_y), left_label, fill=0, font=label_font)  # Black for maximum visibility
            
            # Right column label (secondary translation) - make it very visible
            right_label = f"({secondary_label})"
            right_label_bbox = draw.textbbox((0, 0), right_label, font=label_font)
            right_label_width = right_label_bbox[2] - right_label_bbox[0]
            right_label_x = right_margin + (column_width // 2) - (right_label_width // 2)
            
            # Ensure labels are visible - use black text
            draw.text((right_label_x, bottom_label_y), right_label, fill=0, font=label_font)  # Black for maximum visibility
            
            self.logger.info(f"Drew translation labels: '{left_label}' at ({left_label_x}, {bottom_label_y}), '{right_label}' at ({right_label_x}, {bottom_label_y})")
            self.logger.info(f"Label positions - Left: x={left_label_x}, Right: x={right_label_x}, Y: {bottom_label_y}, Max Y allowed: {max_label_y}")
        else:
            self.logger.warning("No font available for translation labels - labels not drawn")
        
        # Add verse reference in bottom-right corner for parallel mode too
        self._add_verse_reference_display(draw, verse_data)
    
    def _add_verse_reference_display(self, draw: ImageDraw.Draw, verse_data: Dict):
        """Add verse reference prominently at the configured position - this is the main time display."""
        # Check if this is devotional mode
        if verse_data.get('is_devotional') or 'devotional_text' in verse_data:
            # For devotional mode, show time before date
            now = datetime.now()
            current_time = verse_data.get('current_time', now.strftime('%I:%M %p'))
            current_date = verse_data.get('current_date', now.strftime('%A, %B %d, %Y'))
            display_text = f"{current_time} - {current_date}"
        elif verse_data.get('is_date_event'):
            # Show the actual date instead of reference for date-based mode
            now = datetime.now()
            display_text = now.strftime('%B %d, %Y')
        elif verse_data.get('is_summary'):
            # For book summaries, show current time in the preferred format
            now = datetime.now()
            time_format = verse_data.get('time_format', '12')
            if time_format == '12':
                display_text = now.strftime('%I:%M').lstrip('0')  # Remove leading zero from hour
            else:
                display_text = now.strftime('%H:%M')
        else:
            # Regular verse mode - show reference (this is the main time component!)
            display_text = verse_data.get('reference', 'Unknown')
        
        # Use reference font for the verse reference display  
        if self.reference_font:
            # Calculate text dimensions first
            ref_bbox = draw.textbbox((0, 0), display_text, font=self.reference_font)
            text_width = ref_bbox[2] - ref_bbox[0]
            text_height = ref_bbox[3] - ref_bbox[1]
            
            # Smart margin calculation based on border presence
            has_decorative_border = self.current_background_index > 0
            base_margin = self.reference_margin
            if has_decorative_border:
                base_margin = max(base_margin, 80)  # Ensure enough margin for decorative borders and transformations
            
            # Calculate position based on reference_position setting
            if self.reference_position == 'bottom-right':
                x = self.width - text_width - base_margin
                y = self.height - text_height - base_margin
            elif self.reference_position == 'bottom-left':
                x = base_margin
                y = self.height - text_height - base_margin
            elif self.reference_position == 'top-right':
                x = self.width - text_width - base_margin
                y = base_margin
            elif self.reference_position == 'top-left':
                x = base_margin
                y = base_margin
            elif self.reference_position == 'center-top':
                x = (self.width - text_width) // 2
                y = base_margin + self.reference_y_offset  # Use the y_offset setting (20 pixels from top)
            elif self.reference_position == 'center-bottom':
                x = (self.width - text_width) // 2
                # Position lower than very bottom - about 80% down for top-middle appearance after rotation
                y = self.height - text_height - (base_margin * 4)
            elif self.reference_position == 'top-center-right':
                # Position in upper area, centered horizontally but offset to the right
                x = (self.width // 2) + (text_width // 2)  # Center + half text width to shift right
                y = base_margin
            else:  # custom or fallback to bottom-right
                x = self.width - text_width - base_margin
                y = self.height - text_height - base_margin
            
            # Apply custom offsets
            x += self.reference_x_offset
            y += self.reference_y_offset
            
            # Ensure text stays within bounds
            x = max(base_margin, min(x, self.width - text_width - base_margin))
            y = max(base_margin, min(y, self.height - text_height - base_margin))
            
            # Note: Frame buffer clearing is now handled in display_manager.py
            # No need for local clearing that can create white rectangles on backgrounds
            
            # Draw the reference at the configured position (prominently at top for center-top)
            draw.text((x, y), display_text, fill=0, font=self.reference_font)