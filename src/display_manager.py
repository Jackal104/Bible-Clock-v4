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
        self.force_refresh_interval = int(os.getenv('FORCE_REFRESH_INTERVAL', '60'))
        
        self.last_image_hash = None
        self.last_full_refresh = time.time()
        self.display_device = None
        
        if not self.simulation_mode:
            self._initialize_hardware()
    
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
        # Determine refresh mode
        if force_refresh or self._should_force_refresh():
            # Full refresh for better quality
            self.display_device.frame_buf.paste(image, (0, 0))
            self.display_device.draw_full(DisplayModes.GC16)
            self.last_full_refresh = time.time()
            self.logger.debug("Full display refresh")
        else:
            # Fast partial refresh
            self.display_device.frame_buf.paste(image, (0, 0))
            self.display_device.draw_partial(DisplayModes.DU)
            self.logger.debug("Partial display refresh")
    
    def _should_force_refresh(self) -> bool:
        """Check if a full refresh is needed based on time interval."""
        return (time.time() - self.last_full_refresh) > (self.force_refresh_interval * 60)
    
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
    
    def show_transient_message(self, state: str, message: str = None, duration: float = 2.0):
        """Show a temporary message overlay on the display."""
        try:
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
            
            # Get display text
            display_text = display_messages.get(state, message or state)
            
            # Create a simple overlay image
            overlay = Image.new('L', (self.width, self.height), 255)  # white background
            draw = ImageDraw.Draw(overlay)
            
            # Use a simple font for the message
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
                except:
                    font = ImageFont.load_default()
            
            # Calculate text size and position
            text_bbox = draw.textbbox((0, 0), display_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Position in top-left corner with padding
            x, y = 30, 30
            
            # Draw white rectangle background with black border
            draw.rectangle((x - 15, y - 15, x + text_width + 30, y + text_height + 30), 
                          fill=255, outline=0, width=4)
            
            # Draw black text
            draw.text((x, y), display_text, font=font, fill=0)
            
            # Display the overlay
            self.display_image(overlay, force_refresh=True)
            
            self.logger.info(f"Showing visual feedback: {state} -> {display_text}")
            
            # Start a timer to restore normal display (only for certain states)
            if state in ["wake_detected", "listening", "recording", "ready"]:
                def restore_display():
                    time.sleep(duration)
                    # Force a display update to clear the message
                    # The next scheduled update will restore normal content
                    self.logger.info("Visual feedback expired")
                
                timer_thread = threading.Thread(target=restore_display, daemon=True)
                timer_thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to show visual feedback: {e}")
    
    def get_display_info(self) -> dict:
        """Get display information."""
        return {
            'width': self.width,
            'height': self.height,
            'rotation': self.rotation,
            'simulation_mode': self.simulation_mode,
            'last_refresh': self.last_full_refresh
        }