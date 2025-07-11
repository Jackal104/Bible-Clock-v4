"""
ChatGPT + Piper TTS Voice Control for Bible Clock
High-quality voice synthesis with AI-powered Bible Q&A
"""

import os
import logging
import threading
import time
import queue
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
import openai

class ChatGPTPiperVoiceControl:
    def __init__(self, verse_manager, image_generator, display_manager):
        self.logger = logging.getLogger(__name__)
        self.verse_manager = verse_manager
        self.image_generator = image_generator
        self.display_manager = display_manager
        
        # Voice settings
        self.enabled = os.getenv('ENABLE_CHATGPT_VOICE', 'false').lower() == 'true'
        self.wake_word = os.getenv('WAKE_WORD', 'bible clock').lower()
        self.voice_timeout = int(os.getenv('VOICE_TIMEOUT', '5'))
        
        # ChatGPT settings
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.chatgpt_model = os.getenv('CHATGPT_MODEL', 'gpt-3.5-turbo')
        self.max_tokens = int(os.getenv('CHATGPT_MAX_TOKENS', '150'))
        self.temperature = float(os.getenv('CHATGPT_TEMPERATURE', '0.7'))
        
        # Piper TTS settings
        self.piper_model = os.getenv('PIPER_VOICE_MODEL', 'en_US-amy-medium.onnx')
        self.piper_speed = float(os.getenv('PIPER_VOICE_SPEED', '1.0'))
        self.piper_volume = float(os.getenv('PIPER_VOICE_VOLUME', '0.9'))
        
        # Voice components
        self.recognizer = None
        self.microphone = None
        self.listening = False
        self.command_queue = queue.Queue()
        
        # Threading
        self.listen_thread = None
        self.command_thread = None
        
        if self.enabled:
            self._initialize_voice_components()
    
    def _initialize_voice_components(self):
        """Initialize speech recognition, ChatGPT, and Piper TTS."""
        try:
            # Initialize OpenAI
            if self.openai_api_key:
                openai.api_key = self.openai_api_key
                self.logger.info("ChatGPT API initialized")
            else:
                self.logger.warning("No OpenAI API key provided")
            
            # Initialize speech recognition
            self._initialize_speech_recognition()
            
            # Test Piper TTS
            self._test_piper_tts()
            
            self.logger.info("ChatGPT + Piper voice control initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Voice control initialization failed: {e}")
            self.enabled = False
    
    def _initialize_speech_recognition(self):
        """Initialize speech recognition."""
        try:
            import speech_recognition as sr
            
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.recognizer.operation_timeout = self.voice_timeout
            
            # Find USB microphone
            mic_index = self._find_usb_microphone()
            if mic_index is not None:
                self.microphone = sr.Microphone(device_index=mic_index)
            else:
                self.microphone = sr.Microphone()
            
            self.logger.info("Speech recognition initialized")
            
        except ImportError:
            self.logger.error("speech_recognition not available. Install with: pip install SpeechRecognition")
        except Exception as e:
            self.logger.error(f"Speech recognition initialization failed: {e}")
    
    def _find_usb_microphone(self):
        """Find USB microphone device index."""
        try:
            import pyaudio
            import speech_recognition as sr
            
            # Get microphone list
            mic_list = sr.Microphone.list_microphone_names()
            
            for i, name in enumerate(mic_list):
                if any(keyword in name.lower() for keyword in ['usb', 'pnp', 'audio', 'fifine']):
                    self.logger.info(f"Found USB microphone: {name} (index {i})")
                    return i
            
            self.logger.warning("USB microphone not found, using default")
            return None
            
        except Exception as e:
            self.logger.warning(f"Error finding USB microphone: {e}")
            return None
    
    def _test_piper_tts(self):
        """Test Piper TTS installation."""
        try:
            model_path = Path.home() / ".local" / "share" / "piper" / "voices" / self.piper_model
            
            if not model_path.exists():
                self.logger.error(f"Piper voice model not found: {model_path}")
                return False
            
            # Test with simple text
            test_text = "Bible Clock voice control ready"
            self._speak_with_piper(test_text)
            
            self.logger.info("Piper TTS test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Piper TTS test failed: {e}")
            return False
    
    def _speak_with_piper(self, text: str):
        """Convert text to speech using Piper TTS."""
        try:
            model_path = Path.home() / ".local" / "share" / "piper" / "voices" / self.piper_model
            
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Run Piper TTS
            result = subprocess.run([
                'piper',
                '--model', str(model_path),
                '--output_file', temp_path
            ], input=text, text=True, capture_output=True)
            
            if result.returncode == 0:
                # Play the audio
                subprocess.run(['aplay', temp_path], check=True)
                self.logger.info(f"Spoke: {text[:50]}...")
            else:
                self.logger.error(f"Piper TTS failed: {result.stderr}")
            
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Piper TTS error: {e}")
    
    def _query_chatgpt(self, question: str) -> str:
        """Send question to ChatGPT and get response."""
        try:
            if not self.openai_api_key:
                return "I need an OpenAI API key to answer questions. Please add it to your environment variables."
            
            # Create Bible-focused prompt
            system_prompt = """You are a helpful Bible study assistant. Provide accurate, thoughtful responses about the Bible, Christianity, and faith. Keep responses concise and meaningful. If asked about verses, provide the text and brief explanation."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
            
            response = openai.ChatCompletion.create(
                model=self.chatgpt_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            answer = response.choices[0].message.content.strip()
            self.logger.info(f"ChatGPT response: {answer[:100]}...")
            return answer
            
        except Exception as e:
            self.logger.error(f"ChatGPT query failed: {e}")
            return f"I'm sorry, I couldn't process your question right now. Error: {str(e)}"
    
    def start_listening(self):
        """Start voice control loop."""
        if not self.enabled or not self.recognizer or not self.microphone:
            self.logger.warning("Cannot start listening - voice control not properly initialized")
            return
        
        if self.listening:
            return
        
        self.listening = True
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        
        # Start command processing thread
        self.command_thread = threading.Thread(target=self._command_processing_loop, daemon=True)
        self.command_thread.start()
        
        # Welcome message
        self._speak_with_piper("Bible Clock voice control with ChatGPT is ready. Say Bible Clock help to learn commands.")
        
        self.logger.info("Started ChatGPT + Piper voice control")
    
    def stop_listening(self):
        """Stop voice control."""
        self.listening = False
        self.logger.info("Stopped ChatGPT + Piper voice control")
    
    def _listen_loop(self):
        """Main listening loop for wake word detection."""
        self.logger.info("ChatGPT voice control listening started")
        
        while self.enabled and self.listening:
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
                        self.logger.info(f"Wake word detected in: {text}")
                        # Remove wake word and process command
                        command = text.replace(self.wake_word, '').strip()
                        if command:
                            self.command_queue.put(command)
                        else:
                            self.command_queue.put("listening")
                    
                except Exception:
                    # Ignore recognition errors during passive listening
                    pass
                    
            except Exception as e:
                if self.listening:
                    self.logger.error(f"Listening error: {e}")
                time.sleep(0.1)
    
    def _command_processing_loop(self):
        """Process commands when wake word is detected."""
        while self.enabled and self.listening:
            try:
                # Wait for commands
                command = self.command_queue.get(timeout=1)
                
                if command == "listening":
                    self._handle_listening_prompt()
                else:
                    self._process_command(command)
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Command processing error: {e}")
    
    def _handle_listening_prompt(self):
        """Handle when wake word is detected but no command given."""
        try:
            self._speak_with_piper("Yes, how can I help you?")
            
            # Listen for the actual command
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=10)
            
            # Recognize the command
            command_text = self.recognizer.recognize_google(audio).lower()
            self.logger.info(f"Command received: {command_text}")
            
            # Process the command
            self._process_command(command_text)
            
        except Exception as e:
            self.logger.warning(f"Could not understand command: {e}")
            self._speak_with_piper("I didn't understand that. Please try again.")
    
    def _process_command(self, command_text: str):
        """Process voice commands."""
        try:
            # Built-in commands
            if any(word in command_text for word in ['help', 'commands']):
                response = "I can help with Bible questions, verses, and basic commands. Try asking: What does John 3:16 say? Or say next verse, previous verse, or refresh display."
                
            elif 'next verse' in command_text or 'next' in command_text:
                self.verse_manager.next_verse()
                current_verse = self.verse_manager.get_current_verse()
                response = f"Next verse: {current_verse.get('reference', '')} - {current_verse.get('text', '')}"
                
            elif 'previous verse' in command_text or 'previous' in command_text:
                self.verse_manager.previous_verse()
                current_verse = self.verse_manager.get_current_verse()
                response = f"Previous verse: {current_verse.get('reference', '')} - {current_verse.get('text', '')}"
                
            elif 'current verse' in command_text or 'read verse' in command_text:
                current_verse = self.verse_manager.get_current_verse()
                if current_verse:
                    response = f"{current_verse.get('reference', '')}: {current_verse.get('text', '')}"
                else:
                    response = "No verse is currently displayed."
                    
            elif 'refresh' in command_text or 'update' in command_text:
                self.display_manager.refresh()
                response = "Display refreshed."
                
            else:
                # Send to ChatGPT for Bible questions
                response = self._query_chatgpt(command_text)
            
            # Speak the response
            if response:
                self._speak_with_piper(response)
                
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")
            self._speak_with_piper("I'm sorry, I encountered an error processing your request.")

# Compatibility alias
BibleClockChatGPTVoiceControl = ChatGPTPiperVoiceControl