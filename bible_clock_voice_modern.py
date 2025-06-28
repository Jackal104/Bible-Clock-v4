#!/usr/bin/env python3
"""
Bible Clock Voice Control - Modern API Compatible Version
NOW DEPRECATED: Use run_voice_assistant.py for the new modular system

This file is kept for backward compatibility but the new modular system
provides better organization, visual feedback, and maintainability.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def show_migration_message():
    """Show message about migrating to new modular system."""
    print("⚠️  MIGRATION NOTICE")
    print("=" * 60)
    print("This script has been refactored into a modular system!")
    print("")
    print("🆕 NEW RECOMMENDED USAGE:")
    print("  python run_voice_assistant.py")
    print("")
    print("✨ NEW FEATURES IN MODULAR SYSTEM:")
    print("  • 📶 Visual feedback for E-ink displays")
    print("  • 🧩 Modular architecture")
    print("  • 📊 Enhanced performance metrics")
    print("  • 🔧 Better error handling")
    print("  • 🎯 Same interrupt mode & VAD")
    print("")
    print("🔄 MIGRATION PATHS:")
    print("  python run_voice_assistant.py          - Standard voice mode")
    print("  python run_voice_assistant.py display  - Voice + display integration") 
    print("  python run_voice_assistant.py metrics  - Performance metrics demo")
    print("")
    print("💡 Your .env configuration and wake word files work unchanged!")
    print("=" * 60)

def run_legacy_mode():
    """Run the legacy voice assistant (fallback compatibility)."""
    print("\n🔧 Running in legacy compatibility mode...")
    print("💡 Consider migrating to: python run_voice_assistant.py\n")
    
    try:
        # Import and run the new modular system
        from voice_assistant import VoiceAssistant
        from visual_feedback import create_visual_feedback_callback
        
        # Initialize with basic visual feedback
        visual_callback = create_visual_feedback_callback()
        
        # Initialize verse manager if available
        verse_manager = None
        try:
            from src.verse_manager import VerseManager
            verse_manager = VerseManager()
        except ImportError:
            logger.warning("Verse manager not available")
        
        # Run voice assistant
        voice_assistant = VoiceAssistant(
            verse_manager=verse_manager,
            visual_feedback_callback=visual_callback
        )
        
        if voice_assistant.enabled:
            print("✅ Legacy mode active - all features available")
            voice_assistant.run_main_loop()
        else:
            print("❌ Voice assistant disabled. Check configuration.")
            
    except ImportError as e:
        print(f"❌ Error importing modular components: {e}")
        print("💡 Please ensure all files are present and try: python run_voice_assistant.py")
    except Exception as e:
        print(f"❌ Legacy mode error: {e}")
        logger.error(f"Legacy mode error: {e}")

def main():
    """Main function - shows migration guidance and provides legacy compatibility."""
    show_migration_message()
    
    # Ask user for their preference
    print("\n🤔 Choose an option:")
    print("  1. Use new modular system (RECOMMENDED)")
    print("  2. Run legacy compatibility mode")
    print("  3. Exit")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\n🚀 Launching new modular system...")
            os.system("python run_voice_assistant.py")
        elif choice == "2":
            run_legacy_mode()
        elif choice == "3":
            print("\n👋 Goodbye!")
            return
        else:
            print("\n❌ Invalid choice. Please use: python run_voice_assistant.py")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Main function error: {e}")
        print(f"\n❌ Error: {e}")
        print("💡 Please try: python run_voice_assistant.py")


if __name__ == "__main__":
    main()