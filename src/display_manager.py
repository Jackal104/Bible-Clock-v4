"""
Manages e-ink display output and simulation.
"""

import os
import logging
import psutil
from PIL import Image, ImageDraw, ImageFont
from typing import Optional
import time
import threading

try:
    from display_constants import DisplayModes
except ImportError:
    from .display_constants import DisplayModes

class DisplayManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.simulation_mode = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'
        self.width = int(os.getenv('DISPLAY_WIDTH', '1872'))
        self.height = int(os.getenv('DISPLAY_HEIGHT', '1404'))
        self.restore_callback = None  # Will be set by service manager
        # Convert rotation to IT8951 expected format
        rotation_setting = os.getenv('DISPLAY_ROTATION', '0')
        if rotation_setting == '0':
            self.rotation = None  # No rotation
        elif rotation_setting == '90':
            self.rotation = 'CW'
        elif rotation_setting == '180':
            self.rotation = 'flip'
        elif rotation_setting == '270':
            self.rotation = 'CCW'
        else:
            self.rotation = None
        self.vcom_voltage = float(os.getenv('DISPLAY_VCOM', '-1.21'))
        self.force_refresh_interval = int(os.getenv('FORCE_REFRESH_INTERVAL', '60'))  # 1 hour to reduce ghosting
        
        self.last_image_hash = None
        self.last_full_refresh = time.time()
        self.partial_refresh_count = 0  # Track partial refreshes for ghosting prevention
        self.max_partial_refreshes = 10  # Force full refresh after N partial refreshes
        self.display_device = None
        
        if not self.simulation_mode:
            self._initialize_hardware()
    
    def set_restore_callback(self, callback):
        """Set callback function to restore normal display."""
        self.restore_callback = callback
    
    def _initialize_hardware(self):
        """Initialize the IT8951 e-ink display."""
        try:
            # Import hardware-specific modules
            from IT8951.display import AutoEPDDisplay
            
            self.display_device = AutoEPDDisplay(
                vcom=self.vcom_voltage,  # VCOM voltage from display ribbon
                rotate=self.rotation,
                spi_hz=24000000
            )
            
            self.logger.info(f"E-ink display initialized: {self.width}x{self.height}")
            
        except ImportError:
            self.logger.warning("IT8951 library not available, falling back to simulation")
            self.simulation_mode = True
        except Exception as e:
            self.logger.error(f"Display initialization failed: {e}")
            self.simulation_mode = True
    
    def display_image(self, image: Image.Image, force_refresh: bool = False):
        """Display image on e-ink screen or save for simulation."""
        try:
            # Resize image to display dimensions
            if image.size != (self.width, self.height):
                image = image.resize((self.width, self.height), Image.Resampling.LANCZOS)
            
            # Convert to grayscale for e-ink
            if image.mode != 'L':
                image = image.convert('L')
            
            # Check if image has changed
            image_hash = hash(image.tobytes())
            needs_update = (
                force_refresh or 
                image_hash != self.last_image_hash or
                self._should_force_refresh()
            )
            
            if not needs_update:
                self.logger.info("Image unchanged, skipping update - forcing refresh anyway")
                # Force update anyway for debugging automatic updates
                needs_update = True
            
            if self.simulation_mode:
                self._simulate_display(image)
                self.logger.info("Display updated (simulation mode)")
            else:
                self._display_on_hardware(image, force_refresh)
                self.logger.info("Display updated (hardware mode)")
            
            self.last_image_hash = image_hash
            self._check_memory_usage()
            
        except Exception as e:
            self.logger.error(f"Display update failed: {e}")
    
    def _simulate_display(self, image: Image.Image):
        """Simulate display by saving image to file."""
        simulation_path = 'current_display.png'
        image.save(simulation_path)
        self.logger.info(f"Display simulated - image saved to {simulation_path}")
    
    def _display_on_hardware(self, image: Image.Image, force_refresh: bool):
        """Display image on actual e-ink hardware."""
        if not self.display_device:
            raise RuntimeError("Display device not initialized")
        
        # Apply mirroring if needed (fixes backwards text)
        mirror_setting = os.getenv('DISPLAY_MIRROR', 'false').lower()
        if mirror_setting == 'true':
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        elif mirror_setting == 'vertical':
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        elif mirror_setting == 'both':
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        
        # Apply software rotation for precise control (since hardware rotation=None)
        # This ensures proper coordinate handling for our text positioning
        if os.getenv('DISPLAY_PHYSICAL_ROTATION', '180') == '180':
            image = image.rotate(180)
        
        # Use our local display constants instead of IT8951 constants
        # Aggressively clear frame buffer to prevent overlapping artifacts
        white_image = Image.new('L', (self.width, self.height), 255)
        self.display_device.frame_buf.paste(white_image, (0, 0))
        # Double clear for stubborn artifacts
        self.display_device.frame_buf.paste(white_image, (0, 0))
        
        # Smart refresh mode - full refresh only when needed
        if force_refresh or self._should_force_refresh():
            # Full refresh for background changes or scheduled refreshes
            self.display_device.frame_buf.paste(image, (0, 0))
            self.display_device.draw_full(DisplayModes.GC16)
            self.last_full_refresh = time.time()
            self.partial_refresh_count = 0  # Reset counter after full refresh
            self.logger.debug("Full display refresh (background change or scheduled)")
        else:
            # Smooth partial refresh for regular verse updates
            self.display_device.frame_buf.paste(image, (0, 0))
            self.display_device.draw_partial(DisplayModes.DU)
            self.partial_refresh_count += 1  # Increment partial refresh counter
            self.logger.debug(f"Partial display refresh (verse update) - count: {self.partial_refresh_count}")
    
    def _should_force_refresh(self) -> bool:
        """Check if a full refresh is needed based on time interval or partial refresh count."""
        time_based = (time.time() - self.last_full_refresh) > (self.force_refresh_interval * 60)
        count_based = self.partial_refresh_count >= self.max_partial_refreshes
        
        if count_based:
            self.logger.info(f"Forcing refresh due to {self.partial_refresh_count} partial refreshes (ghosting prevention)")
        
        return time_based or count_based
    
    def _check_memory_usage(self):
        """Monitor memory usage and trigger garbage collection if needed."""
        memory_percent = psutil.virtual_memory().percent
        threshold = int(os.getenv('MEMORY_THRESHOLD', '80'))
        
        if memory_percent > threshold:
            import gc
            gc.collect()
            self.logger.warning(f"High memory usage ({memory_percent}%), garbage collection triggered")
    
    def clear_display(self):
        """Clear the display to white."""
        white_image = Image.new('L', (self.width, self.height), 255)
        self.display_image(white_image, force_refresh=True)
    
    def clear_ghosting(self):
        """Aggressive ghosting removal with multiple refresh cycles."""
        if self.simulation_mode:
            self.logger.info("Simulation mode - would clear ghosting")
            return
            
        try:
            self.logger.info("Starting aggressive ghosting removal")
            
            # Create full black then full white images
            black_image = Image.new('L', (self.width, self.height), 0)
            white_image = Image.new('L', (self.width, self.height), 255)
            
            # Multiple refresh cycles to remove ghosting
            for cycle in range(3):
                self.logger.info(f"Ghosting removal cycle {cycle + 1}/3")
                
                # Black refresh
                self.display_device.frame_buf.paste(black_image, (0, 0))
                self.display_device.draw_full(DisplayModes.GC16)
                time.sleep(1)
                
                # White refresh
                self.display_device.frame_buf.paste(white_image, (0, 0))
                self.display_device.draw_full(DisplayModes.GC16)
                time.sleep(1)
            
            self.last_full_refresh = time.time()
            self.partial_refresh_count = 0
            self.logger.info("Ghosting removal completed")
            
        except Exception as e:
            self.logger.error(f"Error during ghosting removal: {e}")
    
    def show_transient_message(self, state: str, message: str = None, duration: float = None):
        """Show a temporary message overlay on the display."""
        try:
            # Handle special restore state
            if state == "restore":
                self.logger.info("🔄 RESTORE STATE RECEIVED - Triggering display restoration to normal Bible verse")
                if self.restore_callback:
                    try:
                        self.logger.info("🔄 Calling restore callback...")
                        self.restore_callback()
                        self.logger.info("✅ Restore callback completed successfully")
                        return
                    except Exception as e:
                        self.logger.error(f"❌ Restore callback failed: {e}")
                # Fallback: just clear to trigger normal display
                self.logger.info("🔄 Using fallback clear display method")
                try:
                    self.clear_display()
                    self.logger.info("✅ Fallback clear display completed")
                except Exception as e:
                    self.logger.error(f"❌ Display restore clear failed: {e}")
                return
            # Map voice states to display messages
            display_messages = {
                "wake_detected": "🎤 Listening...",
                "listening": "🎤 Listening...",
                "recording": "🎙️ Recording...",
                "processing": "💭 Processing...",
                "thinking": "🤔 Thinking...",
                "speaking": "🔊 Speaking...",
                "ready": "✅ Ready",
                "error": "❌ Error",
                "interrupted": "⏸️ Interrupted"
            }
            
            # Set state-specific durations if not provided
            if duration is None:
                state_durations = {
                    "speaking": 15.0,      # Longer for TTS - up to 15 seconds
                    "ai_response": 10.0,   # Longer for AI responses
                    "processing": 8.0,     # Longer for processing
                    "thinking": 5.0,       # Medium for thinking
                    "wake_detected": 3.0,  # Short for wake detection
                    "listening": 5.0,      # Medium for listening
                    "recording": 5.0,      # Medium for recording
                    "ready": 2.0,          # Short for ready state
                    "error": 4.0,          # Medium for errors
                    "interrupted": 2.0     # Short for interruptions
                }
                duration = state_durations.get(state, 2.0)  # Default 2 seconds
            
            # Get display text - special handling for AI responses
            if state == "ai_response" and message:
                display_text = message
            else:
                display_text = display_messages.get(state, message or state)
            
            # Create a simple overlay image
            overlay = Image.new('L', (self.width, self.height), 255)  # white background
            draw = ImageDraw.Draw(overlay)
            
            # Use appropriate font size based on content type
            if state == "ai_response":
                # Smaller font for AI responses to fit more text
                font_size = 32
            else:
                # Larger font for status messages
                font_size = 48
                
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Handle text wrapping for AI responses
            if state == "ai_response":
                wrapped_lines = self._wrap_text_for_display(display_text, font, self.width - 60)
                display_text = "\n".join(wrapped_lines)
            
            # Calculate text size and position
            if "\n" in display_text:
                # Multi-line text
                lines = display_text.split("\n")
                line_heights = []
                max_width = 0
                for line in lines:
                    line_bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = line_bbox[2] - line_bbox[0]
                    line_height = line_bbox[3] - line_bbox[1]
                    line_heights.append(line_height)
                    max_width = max(max_width, line_width)
                text_width = max_width
                text_height = sum(line_heights) + (len(lines) - 1) * 10  # 10px line spacing
            else:
                # Single line text
                text_bbox = draw.textbbox((0, 0), display_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
            
            # Position based on display transforms: mirror=true + rotation=180 means we need bottom-right initially
            mirror_setting = os.getenv('DISPLAY_MIRROR', 'false').lower()
            rotation_setting = os.getenv('DISPLAY_PHYSICAL_ROTATION', '0')
            
            if mirror_setting == 'true' and rotation_setting == '180':
                # Position in bottom-right so after flip + 180° rotation it ends up top-left
                x = self.width - text_width - 30
                y = self.height - text_height - 30
            else:
                # Default position
                x, y = 30, 30
            
            # Check if we need to rotate the text itself
            if mirror_setting == 'true' and rotation_setting == '180':
                # Create a temporary image for the text with some padding
                text_padding = 20
                text_img_width = text_width + (text_padding * 2)
                text_img_height = text_height + (text_padding * 2)
                text_img = Image.new('L', (text_img_width, text_img_height), 255)
                text_draw = ImageDraw.Draw(text_img)
                
                # Draw text on temporary image
                text_draw.text((text_padding, text_padding), display_text, font=font, fill=0)
                
                # Rotate the text image 180 degrees
                text_img = text_img.rotate(180)
                
                # Draw white rectangle background with black border on main overlay
                draw.rectangle((x - 15, y - 15, x + text_width + 30, y + text_height + 30), 
                              fill=255, outline=0, width=4)
                
                # Paste the rotated text onto the overlay
                # Adjust position to account for the rotated text placement
                paste_x = x - text_padding
                paste_y = y - text_padding
                overlay.paste(text_img, (paste_x, paste_y))
            else:
                # Draw normally
                # Draw white rectangle background with black border
                draw.rectangle((x - 15, y - 15, x + text_width + 30, y + text_height + 30), 
                              fill=255, outline=0, width=4)
                
                # Draw text (handle multi-line for AI responses)
                if "\n" in display_text:
                    self._draw_multiline_text(draw, (x, y), display_text, font, fill=0)
                else:
                    draw.text((x, y), display_text, font=font, fill=0)
            
            # Display the overlay (transforms will be applied in _display_on_hardware)
            self.display_image(overlay, force_refresh=True)
            
            self.logger.info(f"Showing visual feedback: {state} -> {display_text}")
            
            # Start a timer to restore normal display (only for certain states)
            if state in ["wake_detected", "listening", "recording", "ready", "ai_response", "speaking"]:
                def restore_display():
                    time.sleep(duration)
                    # Force a display update to clear the message
                    self.logger.info("Visual feedback expired - restoring normal display")
                    # Use callback to restore display if available
                    if self.restore_callback:
                        try:
                            self.restore_callback()
                        except Exception as e:
                            self.logger.error(f"Failed to restore display after visual feedback: {e}")
                    else:
                        # Fallback: just clear with a white screen
                        try:
                            self.clear_display()
                        except Exception as e:
                            self.logger.error(f"Failed to clear display after visual feedback: {e}")
                
                timer_thread = threading.Thread(target=restore_display, daemon=True)
                timer_thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to show visual feedback: {e}")
    
    def _wrap_text_for_display(self, text: str, font, max_width: int) -> list:
        """Wrap text to fit within display width."""
        import textwrap
        
        # Calculate average character width
        sample_text = "W" * 10  # Use wide character for measurement
        sample_bbox = ImageDraw.Draw(Image.new('L', (100, 100))).textbbox((0, 0), sample_text, font=font)
        avg_char_width = (sample_bbox[2] - sample_bbox[0]) / len(sample_text)
        
        # Calculate approximate characters per line
        chars_per_line = int(max_width / avg_char_width) - 2  # Add buffer
        
        # Wrap text
        wrapped = textwrap.fill(text, width=max(chars_per_line, 20))  # Minimum 20 chars per line
        return wrapped.split('\n')
    
    def _draw_multiline_text(self, draw, position: tuple, text: str, font, fill=0):
        """Draw multi-line text on the display."""
        x, y = position
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_y = y + (i * 40)  # 40px line spacing
            if line_y < self.height - 40:  # Don't draw beyond display bounds
                draw.text((x, line_y), line, font=font, fill=fill)
    
    def get_display_info(self) -> dict:
        """Get display information."""
        return {
            'width': self.width,
            'height': self.height,
            'rotation': self.rotation,
            'simulation_mode': self.simulation_mode,
            'last_refresh': self.last_full_refresh
        }