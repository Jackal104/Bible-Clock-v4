#!/usr/bin/env python3
"""
Main entry point for the Bible Clock application.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from service_manager import ServiceManager
from display_manager import DisplayManager
from verse_manager import VerseManager
from image_generator import ImageGenerator
from voice_control import VoiceControl
from web_interface.app import create_app
import threading
import time

def setup_logging():
    """Configure logging based on environment settings."""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('LOG_FILE', 'bible-clock.log')
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def display_splash_screen(display_manager, image_generator):
    """Display welcome splash screen on startup."""
    try:
        splash_text = "Welcome to your Bible Clock\n\nWith all my love,\nMatt"
        image = image_generator.create_splash_image(splash_text)
        display_manager.display_image(image)
        time.sleep(3)  # Show splash for 3 seconds
    except Exception as e:
        logging.error(f"Error displaying splash screen: {e}")

def main():
    parser = argparse.ArgumentParser(description='Bible Clock Application')
    parser.add_argument('--simulate', action='store_true', 
                       help='Run in simulation mode (no hardware required)')
    parser.add_argument('--no-voice', action='store_true',
                       help='Disable voice control')
    parser.add_argument('--no-web', action='store_true',
                       help='Disable web interface')
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Override simulation mode if specified
    if args.simulate:
        os.environ['SIMULATION_MODE'] = 'true'
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize components
        logger.info("Initializing Bible Clock...")
        
        display_manager = DisplayManager()
        verse_manager = VerseManager()
        image_generator = ImageGenerator()
        
        # Display splash screen
        display_splash_screen(display_manager, image_generator)
        
        # Initialize optional components
        voice_control = None
        if not args.no_voice and os.getenv('ENABLE_VOICE', 'false').lower() == 'true':
            try:
                voice_control = VoiceControl(verse_manager, image_generator, display_manager)
                logger.info("Voice control initialized")
            except Exception as e:
                logger.warning(f"Voice control initialization failed: {e}")
        
        # Start web interface if enabled
        web_thread = None
        if not args.no_web and os.getenv('WEB_ENABLED', 'true').lower() == 'true':
            try:
                app = create_app(verse_manager)
                web_thread = threading.Thread(
                    target=lambda: app.run(
                        host=os.getenv('WEB_HOST', '0.0.0.0'),
                        port=int(os.getenv('WEB_PORT', 5000)),
                        debug=False
                    ),
                    daemon=True
                )
                web_thread.start()
                logger.info("Web interface started")
            except Exception as e:
                logger.warning(f"Web interface initialization failed: {e}")
        
        # Initialize and start service manager
        service_manager = ServiceManager(
            verse_manager=verse_manager,
            image_generator=image_generator,
            display_manager=display_manager,
            voice_control=voice_control
        )
        
        logger.info("Bible Clock started successfully")
        service_manager.run()
        
    except KeyboardInterrupt:
        logger.info("Bible Clock stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()