"""
Porcupine-based wake word detection for Bible Clock voice control.
Uses Picovoice Porcupine for efficient, accurate wake word detection.
"""

import os
import logging
import threading
import time
import queue
import numpy as np
from typing import Optional, Callable, Dict, Any, List

class PorcupineVoiceControl:
    def __init__(self, verse_manager, image_generator, display_manager):
        self.logger = logging.getLogger(__name__)
        self.verse_manager = verse_manager
        self.image_generator = image_generator
        self.display_manager = display_manager
        
        # Voice settings
        self.enabled = os.getenv('ENABLE_VOICE', 'false').lower() == 'true'
        self.wake_word = os.getenv('WAKE_WORD', 'bible clock').lower()
        self.voice_rate = int(os.getenv('VOICE_RATE', '150'))
        self.voice_volume = float(os.getenv('VOICE_VOLUME', '0.8'))
        self.voice_timeout = int(os.getenv('VOICE_TIMEOUT', '5'))
        self.phrase_limit = int(os.getenv('VOICE_PHRASE_LIMIT', '15'))
        
        # USB Audio settings
        self.usb_audio_enabled = os.getenv('USB_AUDIO_ENABLED', 'true').lower() == 'true'
        self.usb_mic_device = os.getenv('USB_MIC_DEVICE_NAME', 'USB PnP Audio Device')
        self.usb_speaker_device = os.getenv('USB_SPEAKER_DEVICE_NAME', 'USB PnP Audio Device')
        
        # Audio input/output controls
        self.audio_input_enabled = os.getenv('AUDIO_INPUT_ENABLED', 'true').lower() == 'true'
        self.audio_output_enabled = os.getenv('AUDIO_OUTPUT_ENABLED', 'true').lower() == 'true'
        
        # Porcupine settings
        self.porcupine_access_key = os.getenv('PORCUPINE_ACCESS_KEY', '')
        self.porcupine_keyword_path = os.getenv('PORCUPINE_KEYWORD_PATH', '')
        self.porcupine_sensitivity = float(os.getenv('PORCUPINE_SENSITIVITY', '0.5'))
        
        # Voice components
        self.porcupine = None
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.listening = False
        self.command_queue = queue.Queue()
        self.audio_stream = None
        self.pyaudio_instance = None
        
        # Threading
        self.listen_thread = None
        self.command_thread = None
        
        if self.enabled:
            self._initialize_voice_components()
    
    def _initialize_voice_components(self):
        """Initialize Porcupine, speech recognition, and TTS."""
        try:
            # Initialize Porcupine for wake word detection
            self._initialize_porcupine()
            
            # Initialize speech recognition for command processing
            self._initialize_speech_recognition()
            
            # Initialize TTS
            self._initialize_tts()
            
            self.logger.info("Porcupine voice control initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Voice control initialization failed: {e}")
            self.enabled = False
    
    def _initialize_porcupine(self):
        """Initialize Porcupine wake word detection."""
        try:
            import pvporcupine
            import pyaudio
            
            # Set up default keywords if no custom keyword provided
            keywords = ['picovoice']  # Default keyword
            keyword_paths = None
            
            # Use custom keyword if provided
            if self.porcupine_keyword_path and os.path.exists(self.porcupine_keyword_path):
                keyword_paths = [self.porcupine_keyword_path]
                keywords = None
                self.logger.info(f"Using custom keyword: {self.porcupine_keyword_path}")
            else:
                self.logger.info("Using default 'picovoice' keyword (change PORCUPINE_KEYWORD_PATH for custom)")
            
            # Initialize Porcupine
            if self.porcupine_access_key:
                self.porcupine = pvporcupine.create(
                    access_key=self.porcupine_access_key,
                    keywords=keywords,
                    keyword_paths=keyword_paths,
                    sensitivities=[self.porcupine_sensitivity] * (1 if keyword_paths else len(keywords))
                )
            else:
                # Try without access key (for testing/demo)
                self.logger.warning("No PORCUPINE_ACCESS_KEY provided, using demo mode")
                self.porcupine = pvporcupine.create(
                    keywords=keywords,
                    keyword_paths=keyword_paths,
                    sensitivities=[self.porcupine_sensitivity] * (1 if keyword_paths else len(keywords))
                )
            
            # Initialize PyAudio for microphone input
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # Find USB microphone device
            mic_device_index = self._find_usb_microphone()
            
            # Create audio stream with error handling
            try:
                self.audio_stream = self.pyaudio_instance.open(
                    rate=self.porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    input_device_index=mic_device_index,
                    frames_per_buffer=self.porcupine.frame_length
                )
                if self.audio_stream is None:
                    raise Exception("Audio stream creation returned None")
            except Exception as e:
                self.logger.error(f"Failed to create audio stream: {e}")
                self.audio_stream = None
                raise e
            
            self.logger.info(f"Porcupine initialized: sample_rate={self.porcupine.sample_rate}, frame_length={self.porcupine.frame_length}")
            
        except ImportError:
            self.logger.error("Porcupine not available. Install with: pip install pvporcupine")
            self.enabled = False
        except Exception as e:
            self.logger.error(f"Porcupine initialization failed: {e}")
            self.enabled = False
    
    def _find_usb_microphone(self):
        """Find USB microphone device index with support for named ALSA devices."""
        try:
            # First, try to use the named ALSA device if configured
            if self.usb_mic_device in ['fifine_input', 'microphone', 'usb_mic']:
                self.logger.info(f"Using named ALSA device: {self.usb_mic_device}")
                # For named devices, try to find corresponding PyAudio device
                device_count = self.pyaudio_instance.get_device_count()
                
                for i in range(device_count):
                    device_info = self.pyaudio_instance.get_device_info_by_index(i)
                    device_name = device_info.get('name', '').lower()
                    
                    # Look for Fifine or USB audio devices
                    if (device_info.get('maxInputChannels', 0) > 0 and
                        ('fifine' in device_name or 
                         'k053' in device_name or
                         'usb' in device_name and 'audio' in device_name)):
                        
                        self.logger.info(f"Found Fifine microphone: {device_info['name']} (index {i})")
                        return i
            
            # Standard device detection
            device_count = self.pyaudio_instance.get_device_count()
            
            for i in range(device_count):
                device_info = self.pyaudio_instance.get_device_info_by_index(i)
                device_name = device_info.get('name', '').lower()
                
                # Check if this is our USB microphone
                if (device_info.get('maxInputChannels', 0) > 0 and
                    (self.usb_mic_device.lower() in device_name or
                     'fifine' in device_name or
                     'k053' in device_name or
                     'usb' in device_name and ('audio' in device_name or 'pnp' in device_name))):
                    
                    self.logger.info(f"Found USB microphone: {device_info['name']} (index {i})")
                    return i
            
            # Fallback to default input device
            default_input = self.pyaudio_instance.get_default_input_device_info()
            self.logger.warning(f"USB microphone not found, using default: {default_input['name']}")
            return default_input['index']
            
        except Exception as e:
            self.logger.warning(f"Error finding USB microphone: {e}")
            return None  # Use default
    
    def _initialize_speech_recognition(self):
        """Initialize speech recognition for command processing."""
        try:
            import speech_recognition as sr
            
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.recognizer.operation_timeout = self.voice_timeout
            
            # Create a separate microphone instance for command recognition
            mic_index = self._find_usb_microphone()
            if mic_index is not None:
                self.microphone = sr.Microphone(device_index=mic_index)
            else:
                self.microphone = sr.Microphone()
            
            self.logger.info("Speech recognition initialized for command processing")
            
        except ImportError:
            self.logger.error("speech_recognition not available. Install with: pip install SpeechRecognition")
        except Exception as e:
            self.logger.error(f"Speech recognition initialization failed: {e}")
    
    def _initialize_tts(self):
        """Initialize text-to-speech."""
        try:
            import pyttsx3
            
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', self.voice_rate)
            self.tts_engine.setProperty('volume', self.voice_volume)
            
            # Set voice preference
            voices = self.tts_engine.getProperty('voices')
            if voices and len(voices) > 1:
                self.tts_engine.setProperty('voice', voices[1].id)
            
            self.logger.info("TTS engine initialized")
            
        except Exception as e:
            self.logger.error(f"TTS initialization failed: {e}")
            self.tts_engine = None
    
    def start_listening(self):
        """Start the wake word detection loop."""
        if not self.enabled or not self.porcupine or self.audio_stream is None:
            self.logger.warning("Cannot start listening - voice control not properly initialized")
            return
        
        if self.listening:
            return
        
        self.listening = True
        
        # Start wake word detection thread
        self.listen_thread = threading.Thread(target=self._porcupine_listen_loop, daemon=True)
        self.listen_thread.start()
        
        # Start command processing thread
        self.command_thread = threading.Thread(target=self._command_processing_loop, daemon=True)
        self.command_thread.start()
        
        self.logger.info("Started Porcupine wake word detection")
    
    def stop_listening(self):
        """Stop voice control."""
        self.listening = False
        
        # Wait for threads to stop properly
        if hasattr(self, 'listen_thread') and self.listen_thread.is_alive():
            try:
                self.listen_thread.join(timeout=2.0)  # Wait up to 2 seconds
            except Exception as e:
                self.logger.warning(f"Error waiting for listen thread to stop: {e}")
        
        if hasattr(self, 'command_thread') and self.command_thread.is_alive():
            try:
                self.command_thread.join(timeout=2.0)  # Wait up to 2 seconds
            except Exception as e:
                self.logger.warning(f"Error waiting for command thread to stop: {e}")
        
        # Safe cleanup with NoneType protection
        if self.audio_stream is not None:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception as e:
                self.logger.warning(f"Error stopping audio stream: {e}")
        
        if self.pyaudio_instance is not None:
            try:
                self.pyaudio_instance.terminate()
            except Exception as e:
                self.logger.warning(f"Error terminating PyAudio: {e}")
        
        if self.porcupine is not None:
            try:
                self.porcupine.delete()
            except Exception as e:
                self.logger.warning(f"Error deleting Porcupine: {e}")
        
        self.logger.info("Stopped Porcupine voice control")
    
    def _porcupine_listen_loop(self):
        """Main Porcupine wake word detection loop."""
        self.logger.info("Porcupine wake word detection started")
        
        while self.enabled and self.listening and self.audio_stream:
            try:
                # Read audio data
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = np.frombuffer(pcm, dtype=np.int16)
                
                # Process with Porcupine
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    self.logger.info("Wake word detected by Porcupine!")
                    # Add wake word detection to command queue
                    self.command_queue.put("wake_word_detected")
                    
            except Exception as e:
                self.logger.error(f"Porcupine listening error: {e}")
                time.sleep(0.1)
    
    def _command_processing_loop(self):
        """Process commands when wake word is detected."""
        while self.enabled and self.listening:
            try:
                # Wait for wake word detection
                command = self.command_queue.get(timeout=1)
                
                if command == "wake_word_detected":
                    self._handle_wake_word_detection()
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Command processing error: {e}")
    
    def _handle_wake_word_detection(self):
        """Handle wake word detection and listen for command."""
        try:
            # Check if voice control is still enabled
            if not self.enabled or not self.listening:
                self.logger.debug("Wake word detected but voice control is disabled - ignoring")
                return
                
            if not self.recognizer or not self.microphone:
                self.logger.warning("Speech recognition not available for command processing")
                return
            
            self.logger.info("Wake word detected, listening for command...")
            
            # Provide audio feedback
            if self.tts_engine:
                self.tts_engine.say("Yes?")
                self.tts_engine.runAndWait()
            
            # Listen for command after wake word
            with self.microphone as source:
                # Adjust for ambient noise briefly
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for the actual command
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Recognize the command
            try:
                command_text = self.recognizer.recognize_google(audio).lower()
                self.logger.info(f"Command received: {command_text}")
                
                # Process the command
                self._process_command(command_text)
                
            except Exception as e:
                self.logger.warning(f"Could not understand command: {e}")
                if self.tts_engine:
                    self.tts_engine.say("I didn't understand that. Please try again.")
                    self.tts_engine.runAndWait()
                
        except Exception as e:
            self.logger.error(f"Wake word handling error: {e}")
    
    def _process_command(self, command_text):
        """Process voice commands."""
        try:
            if 'help' in command_text:
                response = "I can help you with Bible verses. Say 'next verse', 'previous verse', 'speak verse', or 'refresh display'."
            elif 'next verse' in command_text or 'next' in command_text:
                self.verse_manager.next_verse()
                response = "Showing next verse."
            elif 'previous verse' in command_text or 'previous' in command_text:
                self.verse_manager.previous_verse()
                response = "Showing previous verse."
            elif 'speak verse' in command_text or 'read verse' in command_text:
                current_verse = self.verse_manager.get_current_verse()
                if current_verse:
                    response = f"{current_verse.get('reference', '')}: {current_verse.get('text', '')}"
                else:
                    response = "No verse available to read."
            elif 'refresh' in command_text or 'update' in command_text:
                self.display_manager.refresh()
                response = "Display refreshed."
            else:
                response = "I'm not sure how to help with that. Say 'help' for available commands."
            
            # Speak the response
            if self.tts_engine and response:
                self.logger.info(f"Speaking: {response}")
                self.tts_engine.say(response)
                self.tts_engine.runAndWait()
                
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")
    
    def test_voice_synthesis(self):
        """Test TTS functionality."""
        if self.tts_engine:
            test_message = "Porcupine voice control is working correctly."
            self.logger.info(f"Testing TTS: {test_message}")
            self.tts_engine.say(test_message)
            self.tts_engine.runAndWait()
        else:
            self.logger.warning("TTS engine not available for testing")

# Compatibility alias
BibleClockVoiceControl = PorcupineVoiceControl