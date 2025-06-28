#!/usr/bin/env python3
"""
Bible Clock - Main Application Entry Point
A Raspberry Pi e-ink display system that shows Bible verses based on time.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from verse_manager import VerseManager
from image_generator import ImageGenerator
from display_manager import DisplayManager
from service_manager import ServiceManager
from voice_assistant import VoiceAssistant as VoiceControl

def setup_logging(level=logging.INFO, log_file=None):
    """Set up logging configuration."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )
    
    # Reduce noise from some libraries
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

def load_environment():
    """Load environment variables from .env file if it exists."""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def validate_environment():
    """Validate required directories and environment setup."""
    required_dirs = [
        'data',
        'images', 
        'src',
        'src/web_interface',
        'src/web_interface/templates',
        'src/web_interface/static'
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            print(f"Error: Required directory '{dir_path}' not found")
            return False
    
    return True

def create_app_components(args):
    """Create and initialize all application components."""
    logger = logging.getLogger(__name__)
    
    # Initialize core components
    verse_manager = VerseManager()
    image_generator = ImageGenerator()
    display_manager = DisplayManager()
    
    # Initialize optional components
    voice_control = None
    if args.enable_voice and not args.disable_voice:
        try:
            voice_control = VoiceControl(
                verse_manager,
                visual_feedback_callback=display_manager.show_transient_message
            )
            logger.info("Voice control enabled")
        except Exception as e:
            logger.warning(f"Voice control initialization failed: {e}")
    
    # Web interface is always available unless explicitly disabled
    web_interface_enabled = not args.disable_web
    
    # Create service manager with all components
    service_manager = ServiceManager(
        verse_manager=verse_manager,
        image_generator=image_generator,
        display_manager=display_manager,
        voice_control=voice_control,
        web_interface=web_interface_enabled
    )
    
    return service_manager

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='Bible Clock - Time-based Bible verse display system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run with default settings
  python main.py --web-only         # Run only web interface
  python main.py --disable-voice    # Run without voice control
  python main.py --debug            # Run with debug logging
  python main.py --log-file app.log # Log to file
        """
    )
    
    # Logging options
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--log-file', type=str,
                        help='Log to specified file')
    
    # Component options
    parser.add_argument('--disable-voice', action='store_true',
                        help='Disable voice control')
    parser.add_argument('--enable-voice', action='store_true',
                        help='Force enable voice control')
    parser.add_argument('--disable-web', action='store_true',
                        help='Disable web interface')
    parser.add_argument('--web-only', action='store_true',
                        help='Run only web interface (no display updates)')
    
    # Configuration options
    parser.add_argument('--simulation', action='store_true',
                        help='Run in simulation mode (save to file instead of e-ink)')
    parser.add_argument('--hardware', action='store_true',
                        help='Force hardware mode (use e-ink display)')
    parser.add_argument('--config', type=str,
                        help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level, args.log_file)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Bible Clock application")
    
    # Load environment configuration
    load_environment()
    
    # Set environment variables based on arguments
    if args.simulation:
        os.environ['SIMULATION_MODE'] = 'true'
    elif args.hardware:
        os.environ['SIMULATION_MODE'] = 'false'
    
    if args.web_only:
        os.environ['WEB_ONLY'] = 'true'
        # Disable display updates in web-only mode
        os.environ['DISABLE_DISPLAY_UPDATES'] = 'true'
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    try:
        # Create application components
        service_manager = create_app_components(args)
        
        # Display startup information
        logger.info("Bible Clock v2.0.0")
        logger.info(f"Simulation mode: {os.getenv('SIMULATION_MODE', 'false')}")
        logger.info(f"Web interface: {'disabled' if args.disable_web else 'enabled'}")
        logger.info(f"Voice control: {'disabled' if args.disable_voice else 'auto'}")
        
        if not args.disable_web:
            web_host = os.getenv('WEB_HOST', 'bible-clock')
            web_port = os.getenv('WEB_PORT', '5000')
            logger.info(f"Web interface will be available at http://{web_host}:{web_port}")
            if web_host == 'bible-clock':
                logger.info(f"Also accessible at http://localhost:{web_port} and http://127.0.0.1:{web_port}")
        
        # Run the service
        service_manager.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Bible Clock application stopped")

if __name__ == '__main__':
    main()