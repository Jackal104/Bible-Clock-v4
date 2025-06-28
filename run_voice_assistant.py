#!/usr/bin/env python3
"""
Bible Clock Voice Assistant - Main Runner
Modular implementation with visual feedback integration
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modular components
from voice_assistant import VoiceAssistant
from visual_feedback import create_visual_feedback_callback, create_eink_visual_feedback

def main():
    """Main function to run the modular voice assistant system."""
    print("🎤 Bible Clock - Modular Voice Assistant System")
    print("=" * 60)
    print("✅ Professional voice interaction")
    print("✅ Interrupt handling & VAD")
    print("✅ Performance metrics")
    print("✅ Visual feedback integration")
    print("✅ Modular architecture")
    print("=" * 60)
    
    try:
        # Initialize verse manager (optional)
        verse_manager = None
        try:
            from src.verse_manager import VerseManager
            verse_manager = VerseManager()
            logger.info("Verse manager loaded")
        except ImportError:
            logger.warning("Verse manager not available - running voice-only mode")
        
        # Create visual feedback callback
        # Option 1: Standard visual feedback
        visual_callback = create_visual_feedback_callback(verse_manager)
        
        # Option 2: E-ink display integration (uncomment if you have E-ink display)
        # eink_display = None  # Replace with actual E-ink display object
        # visual_callback = create_eink_visual_feedback(eink_display)
        
        # Initialize voice assistant with visual feedback
        voice_assistant = VoiceAssistant(
            verse_manager=verse_manager,
            visual_feedback_callback=visual_callback
        )
        
        if not voice_assistant.enabled:
            print("❌ Voice assistant disabled. Check configuration.")
            return
        
        # Show system status
        if voice_assistant.porcupine:
            print("🎯 Wake word: 'Bible Clock' (Custom Porcupine Model) - Ready!")
        else:
            print(f"🎯 Wake word: '{voice_assistant.wake_word}' (Google SR fallback) - Ready!")
        
        print("\\n🎯 VOICE COMMANDS:")
        print("• 'explain this verse' - Current verse explanation")  
        print("• 'what does john 3:16 say' - Bible questions")
        print("• 'next verse' / 'previous verse' - Navigation")
        print("• 'read current verse' - Hear current verse")
        print("• Say 'Bible Clock' during responses to interrupt")
        print("• Press Ctrl+C to exit")
        print("=" * 60)
        
        # Run main voice interaction loop
        voice_assistant.run_main_loop()
    
    except KeyboardInterrupt:
        print("\\n👋 Bible Clock voice assistant stopped.")
        logger.info("Voice assistant stopped by user")
    except Exception as e:
        print(f"\\n❌ Error: {e}")
        logger.error(f"Main error: {e}")
    
    print("\\n👋 Voice assistant shutdown complete.")


def run_with_display_integration():
    """Run voice assistant with full display integration."""
    # This function shows how to integrate with the main Bible clock display
    print("🖥️ Bible Clock - Voice + Display Integration")
    print("=" * 60)
    
    try:
        # Initialize main display components
        verse_manager = None
        try:
            from src.verse_manager import VerseManager
            verse_manager = VerseManager()
        except ImportError:
            logger.error("Verse manager required for display integration")
            return
        
        # Create enhanced visual feedback with display integration
        def display_integrated_callback(state: str, message: str = ""):
            """Visual callback that updates both voice status and main display."""
            logger.info(f"Display Integration: {state} - {message}")
            
            # Update main display with voice state
            # This could overlay voice status on the Bible display
            if hasattr(verse_manager, 'set_voice_overlay'):
                verse_manager.set_voice_overlay(state, message)
            
            # You could also update a separate status area on the display
            # or show visual indicators for different voice states
        
        # Initialize voice assistant with display integration
        voice_assistant = VoiceAssistant(
            verse_manager=verse_manager,
            visual_feedback_callback=display_integrated_callback
        )
        
        if not voice_assistant.enabled:
            print("❌ Voice assistant disabled.")
            return
        
        print("🎯 Voice assistant with display integration ready!")
        print("📊 Performance metrics will be logged")
        print("🔥 Interrupt mode active (say 'Bible Clock' to interrupt)")
        print("=" * 60)
        
        # Run the integrated system
        voice_assistant.run_main_loop()
        
    except Exception as e:
        logger.error(f"Display integration error: {e}")
        print(f"❌ Integration error: {e}")


def show_performance_metrics():
    """Demonstrate performance metrics collection."""
    print("📊 Voice Assistant Performance Metrics Demo")
    print("=" * 50)
    
    # This would be called after voice interactions to show metrics
    # Example metrics output:
    example_metrics = {
        'wake_to_command': 0.15,
        'command_duration': 1.2,
        'gpt_response_time': 0.87,
        'gpt_to_speech': 0.31,
        'total_interaction': 4.23
    }
    
    print("📊 Latest Interaction Metrics:")
    print(f"  Total interaction: {example_metrics['total_interaction']:.2f}s")
    print(f"  Wake → Command: {example_metrics['wake_to_command']:.2f}s")
    print(f"  Command duration: {example_metrics['command_duration']:.2f}s")
    print(f"  GPT response: {example_metrics['gpt_response_time']:.2f}s")
    print(f"  GPT → Speech: {example_metrics['gpt_to_speech']:.2f}s")
    print("\\n💡 Metrics are automatically logged during voice interactions")


if __name__ == "__main__":
    # Check command line arguments for different modes
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "display":
            run_with_display_integration()
        elif mode == "metrics":
            show_performance_metrics()
        elif mode == "help":
            print("🎤 Bible Clock Voice Assistant Modes:")
            print("  python run_voice_assistant.py          - Standard voice mode")
            print("  python run_voice_assistant.py display  - Voice + display integration")
            print("  python run_voice_assistant.py metrics  - Show metrics demo")
            print("  python run_voice_assistant.py help     - Show this help")
        else:
            print(f"❌ Unknown mode: {mode}")
            print("Use 'python run_voice_assistant.py help' for available modes")
    else:
        # Default: run standard voice assistant
        main()