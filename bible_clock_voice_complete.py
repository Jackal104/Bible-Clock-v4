#!/usr/bin/env python3
"""
Complete Bible Clock Voice Control System
Integrates Porcupine wake word detection, ChatGPT, and Piper TTS with USB audio
"""

import os
import sys
import logging
import threading
import time
import queue
import subprocess
import tempfile
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

class BibleClockVoiceSystem:
    def __init__(self):
        """Initialize the complete voice control system."""
        self.enabled = os.getenv('ENABLE_CHATGPT_VOICE', 'true').lower() == 'true'
        self.wake_word = os.getenv('WAKE_WORD', 'Bible Clock').lower()
        self.voice_timeout = int(os.getenv('VOICE_TIMEOUT', '10'))
        
        # Audio device configuration
        self.usb_speaker_device = 'plughw:1,0'  # UACDemoV1.0 speakers
        self.usb_mic_device = 'USB PnP Audio Device'  # Fifine microphone
        
        # API configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.chatgpt_model = os.getenv('CHATGPT_MODEL', 'gpt-3.5-turbo')
        self.max_tokens = int(os.getenv('CHATGPT_MAX_TOKENS', '150'))
        
        # Piper TTS configuration
        self.piper_model_path = os.path.expanduser('~/.local/share/piper/voices/en_US-amy-medium.onnx')
        
        # Voice components
        self.verse_manager = None
        self.listening = False
        self.command_queue = queue.Queue()
        
        if self.enabled:
            self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all voice control components."""
        try:
            # Initialize verse manager
            from src.verse_manager import VerseManager
            self.verse_manager = VerseManager()
            logger.info("Verse manager initialized")
            
            # Test Piper TTS
            if not Path(self.piper_model_path).exists():
                logger.error(f"Amy voice model not found: {self.piper_model_path}")
                return False
            
            # Test speech recognition
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.recognizer.operation_timeout = self.voice_timeout
            
            # Find microphone
            self.microphone = self._find_microphone()
            if not self.microphone:
                logger.error("Could not initialize microphone")
                return False
            
            # Test ChatGPT API
            if not self.openai_api_key:
                logger.warning("No OpenAI API key configured")
            else:
                import openai
                openai.api_key = self.openai_api_key
                logger.info("ChatGPT API initialized")
            
            logger.info("All voice components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Voice system initialization failed: {e}")
            self.enabled = False
            return False
    
    def _find_microphone(self):
        """Find and configure the USB microphone."""
        try:
            import speech_recognition as sr
            
            # Get microphone list
            mic_list = sr.Microphone.list_microphone_names()
            
            # Look for USB microphone
            for i, name in enumerate(mic_list):
                if any(keyword in name.lower() for keyword in ['usb', 'pnp', 'audio', 'fifine']):
                    logger.info(f"Found USB microphone: {name} (index {i})")
                    return sr.Microphone(device_index=i)
            
            # Fallback to default
            logger.warning("USB microphone not found, using default")
            return sr.Microphone()
            
        except Exception as e:
            logger.error(f"Error finding microphone: {e}")
            return None
    
    def speak_with_amy(self, text):
        """Convert text to speech using Piper Amy voice with correct audio routing."""
        try:
            logger.info(f"Speaking: {text[:50]}...")
            
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate audio with Piper
            result = subprocess.run([
                'piper',
                '--model', self.piper_model_path,
                '--output_file', temp_path
            ], input=text, text=True, capture_output=True)
            
            if result.returncode == 0:
                # Play audio through correct USB speakers
                subprocess.run(['aplay', '-D', self.usb_speaker_device, temp_path], 
                             capture_output=True)
                logger.info("Audio played successfully")
            else:
                logger.error(f"Piper TTS failed: {result.stderr}")
            
            # Clean up
            os.unlink(temp_path)
            
        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
    
    def query_chatgpt(self, question):
        """Send question to ChatGPT and get response."""
        try:
            if not self.openai_api_key:
                return "I need an OpenAI API key to answer questions. Please configure it in your environment."
            
            import openai
            
            # Get current verse context
            current_verse = ""
            if self.verse_manager:
                verse_data = self.verse_manager.get_current_verse()
                if verse_data:
                    current_verse = f"Current verse displayed: {verse_data.get('reference', '')} - {verse_data.get('text', '')}"
            
            # Create Bible-focused prompt
            system_prompt = f"""You are a knowledgeable Bible study assistant. Provide accurate, thoughtful responses about the Bible, Christianity, and faith. Keep responses concise and meaningful, suitable for voice interaction.
            
{current_verse}

When asked to "explain this verse" or similar, refer to the current verse displayed above."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
            
            response = openai.ChatCompletion.create(
                model=self.chatgpt_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info(f"ChatGPT response: {answer[:100]}...")
            return answer
            
        except Exception as e:
            logger.error(f"ChatGPT query failed: {e}")
            return f"I'm sorry, I encountered an error processing your question: {str(e)}"
    
    def listen_for_wake_word(self):
        """Listen for the wake word using speech recognition."""
        logger.info(f"Listening for wake word: '{self.wake_word}'")
        
        while self.listening:
            try:
                with self.microphone as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Listen for wake word
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                
                # Recognize speech
                try:
                    text = self.recognizer.recognize_google(audio).lower()
                    
                    if self.wake_word in text:
                        logger.info(f"Wake word detected in: {text}")
                        self.command_queue.put("wake_word_detected")
                    
                except Exception:
                    # Ignore recognition errors during passive listening
                    pass
                    
            except Exception as e:
                if self.listening:
                    logger.debug(f"Listening error: {e}")
                time.sleep(0.1)
    
    def process_commands(self):
        """Process voice commands when wake word is detected."""
        while self.listening:
            try:
                # Wait for wake word detection
                command = self.command_queue.get(timeout=1)
                
                if command == "wake_word_detected":
                    self._handle_voice_command()
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Command processing error: {e}")
    
    def _handle_voice_command(self):
        """Handle voice command after wake word detection."""
        try:
            # Respond to wake word
            self.speak_with_amy("Yes, how can I help you?")
            
            # Listen for the actual command
            logger.info("Listening for command...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=10)
            
            # Recognize the command
            command_text = self.recognizer.recognize_google(audio).lower()
            logger.info(f"Command received: {command_text}")
            
            # Process the command
            self._process_voice_command(command_text)
            
        except Exception as e:
            logger.warning(f"Could not understand command: {e}")
            self.speak_with_amy("I didn't understand that. Please try again.")
    
    def _process_voice_command(self, command_text):
        """Process the voice command."""
        try:
            # Built-in commands
            if any(word in command_text for word in ['help', 'commands']):
                response = "I can help with Bible questions, verses, and basic commands. Try asking: What does John 3:16 say? Or say next verse, previous verse, or refresh display."
                
            elif 'next verse' in command_text or 'next' in command_text:
                if self.verse_manager:
                    self.verse_manager.next_verse()
                    current_verse = self.verse_manager.get_current_verse()
                    response = f"Next verse: {current_verse.get('reference', '')} - {current_verse.get('text', '')}"
                else:
                    response = "Verse manager not available."
                
            elif 'previous verse' in command_text or 'previous' in command_text:
                if self.verse_manager:
                    self.verse_manager.previous_verse()
                    current_verse = self.verse_manager.get_current_verse()
                    response = f"Previous verse: {current_verse.get('reference', '')} - {current_verse.get('text', '')}"
                else:
                    response = "Verse manager not available."
                
            elif any(phrase in command_text for phrase in ['current verse', 'read verse', 'this verse']):
                if self.verse_manager:
                    current_verse = self.verse_manager.get_current_verse()
                    if current_verse:
                        response = f"{current_verse.get('reference', '')}: {current_verse.get('text', '')}"
                    else:
                        response = "No verse is currently displayed."
                else:
                    response = "Verse manager not available."
                    
            elif any(phrase in command_text for phrase in ['explain this verse', 'explain verse', 'what does this mean']):
                # Send current verse explanation to ChatGPT
                if self.verse_manager:
                    current_verse = self.verse_manager.get_current_verse()
                    if current_verse:
                        explanation_query = f"Explain this Bible verse: {current_verse.get('reference', '')} - {current_verse.get('text', '')}"
                        response = self.query_chatgpt(explanation_query)
                    else:
                        response = "No verse is currently displayed to explain."
                else:
                    response = "Verse manager not available."
                
            else:
                # Send to ChatGPT for Bible questions
                response = self.query_chatgpt(command_text)
            
            # Speak the response
            if response:
                self.speak_with_amy(response)
                
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            self.speak_with_amy("I'm sorry, I encountered an error processing your request.")
    
    def start_listening(self):
        """Start the complete voice control system."""
        if not self.enabled:
            logger.warning("Voice control is disabled")
            return
        
        self.listening = True
        
        # Start background threads
        wake_word_thread = threading.Thread(target=self.listen_for_wake_word, daemon=True)
        command_thread = threading.Thread(target=self.process_commands, daemon=True)
        
        wake_word_thread.start()
        command_thread.start()
        
        # Welcome message
        self.speak_with_amy("Bible Clock voice control with ChatGPT is ready. Say Bible Clock to begin.")
        
        logger.info("Voice control system started")
        logger.info(f"Wake word: '{self.wake_word}'")
        logger.info(f"USB Speaker: {self.usb_speaker_device}")
        logger.info(f"USB Microphone: {self.usb_mic_device}")
        
        return wake_word_thread, command_thread
    
    def stop_listening(self):
        """Stop the voice control system."""
        self.listening = False
        logger.info("Voice control system stopped")

def main():
    """Main function to run the voice control system."""
    try:
        # Initialize the voice system
        voice_system = BibleClockVoiceSystem()
        
        if not voice_system.enabled:
            print("Voice control is disabled. Check your configuration.")
            return
        
        print("Starting Bible Clock Voice Control System...")
        print("=" * 50)
        print(f"Wake word: '{voice_system.wake_word}'")
        print(f"Speaker: {voice_system.usb_speaker_device}")
        print(f"Microphone: {voice_system.usb_mic_device}")
        print("=" * 50)
        
        # Start the voice control system
        threads = voice_system.start_listening()
        
        if threads:
            print("\nVoice control system is running!")
            print("Say 'Bible Clock' followed by:")
            print("  • 'Explain this verse' - Get explanation of current verse")
            print("  • 'What does John 3:16 say?' - Ask Bible questions")
            print("  • 'Next verse' / 'Previous verse' - Navigate verses")
            print("  • 'Read current verse' - Hear the current verse")
            print("\nPress Ctrl+C to stop...")
            
            try:
                # Keep the main thread alive
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping voice control system...")
                voice_system.stop_listening()
                print("Voice control stopped.")
        else:
            print("Failed to start voice control system.")
    
    except Exception as e:
        logger.error(f"Main execution error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()