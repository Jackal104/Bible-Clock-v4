"""
Enhanced Bible Clock voice control with comprehensive help system and ChatGPT integration.
Now supports Porcupine for efficient wake word detection.
"""

import os
import logging
import threading
import time
import json
from typing import Optional, Callable, Dict, Any, List
import queue
from datetime import datetime

class BibleClockVoiceControl:
    """
    Bible Clock voice control with automatic Porcupine/SpeechRecognition selection.
    Uses Porcupine for wake word detection if available, falls back to SpeechRecognition.
    """
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
        self.help_enabled = os.getenv('VOICE_HELP_ENABLED', 'true').lower() == 'true'
        self.help_section_pause = int(os.getenv('HELP_SECTION_PAUSE', '2'))
        
        # USB Audio settings (primary audio method)
        self.usb_audio_enabled = os.getenv('USB_AUDIO_ENABLED', 'true').lower() == 'true'
        self.usb_mic_device = os.getenv('USB_MIC_DEVICE_NAME', 'USB PnP Audio Device')
        self.usb_speaker_device = os.getenv('USB_SPEAKER_DEVICE_NAME', 'USB PnP Audio Device')
        
        # Audio input/output controls
        self.audio_input_enabled = os.getenv('AUDIO_INPUT_ENABLED', 'true').lower() == 'true'
        self.audio_output_enabled = os.getenv('AUDIO_OUTPUT_ENABLED', 'true').lower() == 'true'
        self.screen_display_enabled = os.getenv('SCREEN_DISPLAY_ENABLED', 'false').lower() == 'true'
        
        # ReSpeaker HAT settings (legacy support, disabled by default)
        self.respeaker_enabled = os.getenv('RESPEAKER_ENABLED', 'false').lower() == 'true'
        self.respeaker_channels = int(os.getenv('RESPEAKER_CHANNELS', '6'))
        self.respeaker_sample_rate = int(os.getenv('RESPEAKER_SAMPLE_RATE', '16000'))
        self.respeaker_chunk_size = int(os.getenv('RESPEAKER_CHUNK_SIZE', '1024'))
        self.force_respeaker_output = os.getenv('FORCE_RESPEAKER_OUTPUT', 'false').lower() == 'true'
        
        # ChatGPT settings
        self.chatgpt_enabled = os.getenv('ENABLE_CHATGPT', 'false').lower() == 'true'
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.chatgpt_model = os.getenv('CHATGPT_MODEL', 'gpt-3.5-turbo')
        self.max_tokens = int(os.getenv('CHATGPT_MAX_TOKENS', '500'))
        self.temperature = float(os.getenv('CHATGPT_TEMPERATURE', '0.7'))
        self.command_timeout = int(os.getenv('COMMAND_TIMEOUT', '30'))
        self.chatgpt_timeout = int(os.getenv('CHATGPT_TIMEOUT', '15'))
        
        # System prompt for ChatGPT
        self.system_prompt = os.getenv('CHATGPT_SYSTEM_PROMPT', 
            "You are a knowledgeable biblical scholar and theologian helping users understand "
            "Bible verses, biblical history, theology, and Christian faith. Keep responses "
            "concise but meaningful, suitable for voice interaction. When referencing the "
            "current verse being displayed, you may refer to it directly.")
        
        # Voice components
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.listening = False
        self.command_queue = queue.Queue()
        self.voice_selection = 'default'  # Store current voice selection
        
        # ChatGPT conversation context
        self.conversation_history = []
        self.current_verse_context = None
        
        # Token usage tracking
        self.token_usage_stats = {
            'total_tokens': 0,
            'total_questions': 0,
            'total_cost': 0.0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'daily_usage': {}
        }
        
        # Help system
        self.help_commands = self._initialize_help_system()
        
        if self.enabled:
            # Try to use Porcupine first, fall back to traditional approach
            if self._try_porcupine_initialization():
                self.logger.info("Using Porcupine-based voice control")
            else:
                self.logger.info("Using traditional speech recognition for wake word")
                self._initialize_voice_components()
            
            if self.chatgpt_enabled:
                self._initialize_chatgpt()
    
    def _try_porcupine_initialization(self):
        """Try to initialize Porcupine voice control."""
        try:
            from porcupine_voice_control import PorcupineVoiceControl
            
            # Create Porcupine instance
            self.porcupine_control = PorcupineVoiceControl(
                self.verse_manager, 
                self.image_generator, 
                self.display_manager
            )
            
            if self.porcupine_control.enabled:
                # Use Porcupine methods
                self.start_listening = self.porcupine_control.start_listening
                self.stop_listening = self.porcupine_control.stop_listening
                self.test_voice_synthesis = self.porcupine_control.test_voice_synthesis
                self._process_command = self.porcupine_control._process_command
                
                # Expose Porcupine state
                self.listening = False  # Will be managed by Porcupine
                self.porcupine_enabled = True
                
                return True
            else:
                self.logger.warning("Porcupine initialization failed, falling back to speech recognition")
                return False
                
        except ImportError:
            self.logger.info("Porcupine not available, using traditional speech recognition")
            return False
        except Exception as e:
            self.logger.warning(f"Porcupine initialization error: {e}")
            return False
    
    def _initialize_voice_components(self):
        """Initialize speech recognition and text-to-speech with USB audio support."""
        try:
            import speech_recognition as sr
            import pyttsx3
            
            # Initialize speech recognition
            self.recognizer = sr.Recognizer()
            
            # Initialize microphone (USB audio preferred, ReSpeaker as fallback)
            if self.usb_audio_enabled:
                self.microphone = self._initialize_usb_microphone()
            elif self.respeaker_enabled:
                self.microphone = self._initialize_respeaker_microphone()
            else:
                self.microphone = sr.Microphone()
            
            # Adjust recognizer settings for better performance
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.recognizer.operation_timeout = self.voice_timeout
            
            # Initialize text-to-speech with better error handling
            try:
                # Configure TTS for USB audio (preferred) or ReSpeaker (legacy)
                if self.usb_audio_enabled and self.audio_output_enabled:
                    # Initialize TTS for USB audio devices
                    self.tts_engine = pyttsx3.init()
                    self.logger.info("TTS engine initialized for USB audio output")
                elif self.respeaker_enabled and self.force_respeaker_output:
                    # Legacy ReSpeaker support
                    self.tts_engine = pyttsx3.init()
                    os.environ['PULSE_PCM_DEVICE'] = 'hw:seeedvoicecard,0'
                    self.logger.info("TTS engine initialized for ReSpeaker output")
                else:
                    self.tts_engine = pyttsx3.init()
                    self.logger.info("TTS engine initialized with default output")
                    
                self.tts_engine.setProperty('rate', self.voice_rate)
                self.tts_engine.setProperty('volume', self.voice_volume)
                
                # Set voice to a pleasant one if available
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Prefer female voices for biblical content (often perceived as more soothing)
                    female_voices = [v for v in voices if 'female' in v.name.lower() or 'woman' in v.name.lower()]
                    if female_voices:
                        self.tts_engine.setProperty('voice', female_voices[0].id)
                    elif len(voices) > 1:
                        self.tts_engine.setProperty('voice', voices[1].id)
                
                if self.respeaker_enabled:
                    self.logger.info("TTS engine initialized with ReSpeaker HAT support")
                else:
                    self.logger.info("TTS engine initialized successfully")
                
            except RuntimeError as e:
                if "espeak" in str(e).lower():
                    self.logger.error("TTS engine requires espeak/espeak-ng. Install with: sudo apt-get install espeak espeak-data")
                    self.logger.info("Voice synthesis disabled - espeak not available")
                else:
                    self.logger.error(f"TTS engine initialization failed: {e}")
                self.tts_engine = None
            except Exception as e:
                self.logger.error(f"TTS engine initialization failed: {e}")
                self.tts_engine = None
            
            # Try to adjust for ambient noise only if microphone is available
            try:
                with self.microphone as source:
                    self.logger.info("Adjusting for ambient noise... Please wait.")
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
            except Exception as e:
                self.logger.warning(f"Could not adjust for ambient noise: {e}")
            
            self.logger.info("Bible Clock voice control initialized (TTS may be limited)")
            
        except ImportError as e:
            self.logger.error(f"Voice control libraries not available: {e}")
            self.logger.info("Install with: pip install pyttsx3 speechrecognition pyaudio")
            self.enabled = False
        except Exception as e:
            self.logger.error(f"Voice control initialization failed: {e}")
            self.enabled = False
    
    def _initialize_usb_microphone(self):
        """Initialize USB audio microphone with proper parameter detection."""
        try:
            import speech_recognition as sr
            import pyaudio
            
            # First try to find the specific device by name
            device_index = None
            device_name = None
            
            # If device name looks like hw:X,Y format, try to find by ALSA name
            if self.usb_mic_device.startswith('hw:'):
                # Convert hw:X,Y to card number for device matching
                try:
                    card_info = self.usb_mic_device.split(':')[1].split(',')[0]
                    for i, name in enumerate(sr.Microphone.list_microphone_names()):
                        if f"card {card_info}" in name.lower() or f"card{card_info}" in name.lower():
                            device_index = i
                            device_name = name
                            break
                except:
                    pass
            
            # If not found by ALSA name, try by device name match
            if device_index is None:
                for i, name in enumerate(sr.Microphone.list_microphone_names()):
                    if (self.usb_mic_device.lower() in name.lower() or 
                        'usb' in name.lower() or 
                        'fifine' in name.lower() or
                        'audio device' in name.lower()):
                        device_index = i
                        device_name = name
                        break
            
            if device_index is not None:
                self.logger.info(f"Found USB audio device at index {device_index}: {device_name}")
                
                # Get device capabilities to set proper parameters
                p = pyaudio.PyAudio()
                try:
                    device_info = p.get_device_info_by_index(device_index)
                    max_input_channels = int(device_info['maxInputChannels'])
                    default_sample_rate = int(device_info['defaultSampleRate'])
                    
                    # Use safe parameters based on device capabilities
                    channels = min(1, max_input_channels)  # Use mono (1 channel)
                    sample_rate = 16000 if default_sample_rate >= 16000 else 8000
                    chunk_size = 1024
                    
                    self.logger.info(f"Device capabilities: {max_input_channels} channels, {default_sample_rate}Hz default rate")
                    self.logger.info(f"Using parameters: {channels} channel(s), {sample_rate}Hz, {chunk_size} chunk size")
                    
                    # Create microphone with detected parameters
                    microphone = sr.Microphone(
                        device_index=device_index,
                        sample_rate=sample_rate,
                        chunk_size=chunk_size
                    )
                    
                    # Test the microphone to ensure it works
                    try:
                        with microphone as source:
                            # Quick test - just open and close
                            pass
                        self.logger.info("USB microphone test successful")
                        return microphone
                    except Exception as test_error:
                        self.logger.warning(f"USB microphone test failed: {test_error}")
                        # Fall back to simpler parameters
                        return sr.Microphone(device_index=device_index)
                        
                finally:
                    p.terminate()
            else:
                self.logger.warning("USB audio device not found, using default microphone")
                return sr.Microphone()
            
        except Exception as e:
            self.logger.error(f"USB microphone initialization failed: {e}")
            self.logger.info("Falling back to default microphone")
            return sr.Microphone()

    def _initialize_respeaker_microphone(self):
        """Initialize ReSpeaker HAT microphone (legacy support)."""
        try:
            import speech_recognition as sr
            
            # Find ReSpeaker device
            for i, device_info in enumerate(sr.Microphone.list_microphone_names()):
                if 'respeaker' in device_info.lower() or 'seeed' in device_info.lower():
                    self.logger.info(f"Found ReSpeaker device: {device_info}")
                    return sr.Microphone(device_index=i, sample_rate=self.respeaker_sample_rate, 
                                       chunk_size=self.respeaker_chunk_size)
            
            # Fallback to default if ReSpeaker not found
            self.logger.warning("ReSpeaker device not found, using default microphone")
            return sr.Microphone()
            
        except Exception as e:
            self.logger.error(f"ReSpeaker initialization failed: {e}")
            return sr.Microphone()
    
    def _initialize_help_system(self):
        """Initialize the comprehensive help system."""
        return {
            "overview": {
                "title": "Bible Clock Voice Control Overview",
                "content": "Welcome to Bible Clock voice control! I can help you control your Bible Clock display, "
                          "answer biblical questions, and provide spiritual guidance. All commands start with "
                          "'Bible Clock' followed by your request. Here are the main categories of commands I understand."
            },
            "display_commands": {
                "title": "Display Control Commands",
                "commands": {
                    "speak verse": "I will read the current verse being displayed aloud",
                    "refresh display": "I will update the display with a fresh verse",
                    "clear display": "I will clear the screen to white",
                    "change background": "I will switch to the next background style", 
                    "cycle mode": "I will change the Bible translation",
                    "change mode": "I will ask what mode you want and switch to it",
                    "time mode": "I will switch to time-based verse selection",
                    "date mode": "I will switch to biblical calendar events",
                    "random mode": "I will switch to random verse inspiration",
                    "parallel mode": "I will toggle parallel translation mode showing two translations",
                    "change translation to [name]": "I will switch to a specific translation like King James or Amplified",
                    "explain this verse": "I will explain the current verse displayed on screen",
                    "what does this verse mean": "I will provide the meaning of the current verse",
                    "chat": "I will start interactive chat mode for biblical questions"
                }
            },
            "information_commands": {
                "title": "Information Commands",
                "commands": {
                    "what time is it": "I will tell you the current time",
                    "system status": "I will report the system health and performance",
                    "current verse": "I will tell you what verse is currently displayed",
                    "current mode": "I will tell you which display mode is active",
                    "current translation": "I will tell you which Bible translation is being used"
                }
            },
            "chatgpt_commands": {
                "title": "Biblical Questions and AI Assistant",
                "content": "I can answer any biblical questions using artificial intelligence. Simply ask naturally after saying 'Bible Clock'. Here are examples:",
                "examples": [
                    "Explain this verse",
                    "What does this verse mean?",
                    "Who was King David?", 
                    "Explain the parable of the prodigal son",
                    "What happened in the book of Exodus?",
                    "Help me understand this passage",
                    "Tell me about biblical love",
                    "Why is this verse important?",
                    "What can I learn from this?",
                    "What is the significance of the cross?",
                    "How should I pray?"
                ]
            },
            "help_commands": {
                "title": "Help Commands",
                "commands": {
                    "help": "I will provide this complete overview of all commands",
                    "help display": "I will explain display control commands",
                    "help information": "I will explain information commands", 
                    "help questions": "I will explain how to ask biblical questions",
                    "help examples": "I will give examples of questions you can ask",
                    "help setup": "I will explain how to set up and configure voice control"
                }
            },
            "setup_help": {
                "title": "Setup and Configuration Help",
                "content": "To configure Bible Clock voice control: First, ensure your microphone is working. "
                          "You can adjust voice speed and volume through the web interface. "
                          "To enable biblical questions, you need an OpenAI API key in your configuration. "
                          "If you're using a ReSpeaker HAT, enable it in the settings. "
                          "The wake word is 'Bible Clock' followed by your command. "
                          "Speak clearly and wait for my response before giving another command."
            }
        }
    
    def _initialize_chatgpt(self):
        """Initialize ChatGPT integration."""
        if not self.openai_api_key:
            self.logger.warning("OpenAI API key not provided, ChatGPT integration disabled")
            self.chatgpt_enabled = False
            return
        
        try:
            # Try to import openai and test connection
            try:
                import openai
                openai.api_key = self.openai_api_key
                
                # Test API connection
                test_response = openai.ChatCompletion.create(
                    model=self.chatgpt_model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10,
                    timeout=5
                )
                
                self.logger.info("ChatGPT integration initialized successfully")
                
            except ImportError:
                self.logger.error("OpenAI library not installed. Install with: pip install openai")
                self.chatgpt_enabled = False
            
        except Exception as e:
            self.logger.error(f"ChatGPT initialization failed: {e}")
            self.chatgpt_enabled = False
    
    def start_listening(self):
        """Start voice control in background thread."""
        if not self.enabled:
            return
        
        self.listening = True
        listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        command_thread = threading.Thread(target=self._command_processor, daemon=True)
        
        listen_thread.start()
        command_thread.start()
        
        self.logger.info("Bible Clock voice control started")
        self._speak("Bible Clock voice control is ready! Say 'Bible Clock help' to learn about all available commands.")
    
    def stop_listening(self):
        """Stop voice control."""
        self.listening = False
        self.logger.info("Bible Clock voice control stopped")
    
    def _listen_loop(self):
        """Main listening loop."""
        # Import here to ensure it's available in this scope
        try:
            import speech_recognition as sr
        except ImportError:
            self.logger.error("speech_recognition not available")
            return
            
        while self.listening:
            # Check if audio input is enabled
            if not self.audio_input_enabled:
                time.sleep(1)
                continue
                
            try:
                with self.microphone as source:
                    self.logger.debug("Listening for 'Bible Clock' wake word...")
                    # Listen for wake word with longer timeout for better phrase detection
                    audio = self.recognizer.listen(
                        source, 
                        timeout=1, 
                        phrase_time_limit=self.phrase_limit
                    )
                
                try:
                    # Recognize speech
                    text = self.recognizer.recognize_google(audio).lower()
                    self.logger.debug(f"Heard: {text}")
                    
                    # Check for wake word "Bible Clock"
                    if self.wake_word in text:
                        self.logger.info(f"Wake word detected: {text}")
                        self._handle_wake_word_detection(text)
                
                except sr.UnknownValueError:
                    pass  # Could not understand audio
                except sr.RequestError as e:
                    self.logger.warning(f"Speech recognition error: {e}")
            
            except sr.WaitTimeoutError:
                pass  # No speech detected
            except Exception as e:
                self.logger.error(f"Listening error: {e}")
                time.sleep(1)
    
    def _handle_wake_word_detection(self, initial_text: str):
        """Handle wake word detection and capture full command."""
        try:
            # Extract command after wake word
            wake_word_index = initial_text.find(self.wake_word)
            initial_command = initial_text[wake_word_index + len(self.wake_word):].strip()
            
            if initial_command and len(initial_command.split()) >= 3:
                # We have a substantial command already - use it
                full_command = initial_command
                self.logger.info(f"Complete command captured: {full_command}")
            else:
                # Command is too short or missing - listen for more
                if initial_command:
                    self.logger.info(f"Partial command detected: '{initial_command}' - listening for more")
                    self._speak("I heard something. Please continue with your full request.")
                else:
                    self._speak("Yes? How may I help you?")
                full_command = self._listen_for_command()
            
            if full_command:
                self.command_queue.put(('process_command', full_command))
            
        except Exception as e:
            self.logger.error(f"Error handling wake word: {e}")
            self._speak("I'm sorry, I didn't understand that. Say 'Bible Clock help' for assistance.")
    
    def _listen_for_command(self) -> Optional[str]:
        """Listen for the actual command after wake word detection."""
        try:
            import speech_recognition as sr
            
            with self.microphone as source:
                self.logger.info("Listening for command...")
                # Listen for longer phrase with extended timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=self.command_timeout, 
                    phrase_time_limit=self.phrase_limit
                )
            
            command = self.recognizer.recognize_google(audio)
            self.logger.info(f"Command received: {command}")
            return command.strip()
            
        except sr.WaitTimeoutError:
            self.logger.info("Command timeout - no speech detected")
            self._speak("I didn't hear anything. Please try again by saying 'Bible Clock' followed by your command.")
            return None
        except sr.UnknownValueError:
            self.logger.info("Could not understand command")
            self._speak("I didn't understand that. Please try again, or say 'Bible Clock help' for assistance.")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition error: {e}")
            self._speak("I'm having trouble with speech recognition. Please check your microphone.")
            return None
    
    def _command_processor(self):
        """Process commands from queue."""
        while self.listening:
            try:
                command_type, command_data = self.command_queue.get(timeout=1)
                
                if command_type == 'process_command':
                    self._process_command(command_data)
                elif command_type == 'speak':
                    self._speak(command_data)
                
                self.command_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Command processing error: {e}")
    
    def _process_command(self, text: str):
        """Process voice commands with help system and ChatGPT integration."""
        text_lower = text.lower().strip()
        
        # Update current verse context
        try:
            self.current_verse_context = self.verse_manager.get_current_verse()
        except Exception as e:
            self.logger.error(f"Error getting current verse: {e}")
        
        # Check for help commands first
        if self._handle_help_commands(text_lower):
            return
        
        # Check for built-in commands
        built_in_commands = {
            'speak verse': self._speak_current_verse,
            'read verse': self._speak_current_verse,
            'current verse': self._speak_current_verse_info,
            'refresh display': self._refresh_display,
            'update display': self._refresh_display,
            'clear display': self._clear_display,
            'change background': self._change_background,
            'next background': self._change_background,
            'cycle mode': self._cycle_translation,
            'change translation': self._cycle_translation,
            'next translation': self._cycle_translation,
            'change mode': self._handle_change_mode_command,
            'time mode': lambda: self._set_display_mode('time'),
            'date mode': lambda: self._set_display_mode('date'),
            'random mode': lambda: self._set_display_mode('random'),
            'parallel mode': self._toggle_parallel_mode,
            'chat': self._start_chat_mode,
            'start chat': self._start_chat_mode,
            'stop chat': self._force_display_restore,
            'exit chat': self._force_display_restore,
            'end chat': self._force_display_restore,
            'clear display': self._force_display_restore,
            'what time is it': self._speak_time,
            'current time': self._speak_time,
            'system status': self._speak_system_status,
            'status': self._speak_system_status,
            'current mode': self._speak_current_mode,
            'current translation': self._speak_current_translation
        }
        
        # Check for specific translation change commands first
        if self._handle_translation_change_command(text_lower):
            return
        
        # Check for exact matches first
        command_executed = False
        for command, action in built_in_commands.items():
            if command in text_lower:
                self.logger.info(f"Built-in command executed: {command}")
                action()
                command_executed = True
                break
        
        if command_executed:
            return
        
        # Check for verse explanation commands first
        verse_explanation_phrases = ['explain this verse', 'explain verse', 'what does this mean', 'explain this', 'what does this verse mean']
        if any(phrase in text_lower for phrase in verse_explanation_phrases):
            if self.chatgpt_enabled:
                try:
                    current_verse = self.verse_manager.get_current_verse()
                    if current_verse:
                        explanation_query = f"Explain this Bible verse: {current_verse.get('reference', '')} - {current_verse.get('text', '')}"
                        self.logger.info(f"Verse explanation request for: {current_verse.get('reference', '')}")
                        self._process_chatgpt_question(explanation_query)
                        return
                    else:
                        self._speak("No verse is currently displayed to explain.")
                        return
                except Exception as e:
                    self.logger.error(f"Error getting current verse for explanation: {e}")
                    self._speak("Sorry, I couldn't access the current verse.")
                    return
            else:
                self._speak("Biblical explanations are not currently enabled. Please check your ChatGPT configuration.")
                return
        
        # Check for ChatGPT question indicators
        question_indicators = [
            'what does', 'what is', 'who is', 'who was', 'explain', 'tell me about',
            'why', 'how', 'where', 'when', 'help me understand',
            'what happened', 'can you explain', 'question about', 'meaning of',
            'significance of', 'importance of', 'teach me', 'show me'
        ]
        
        is_question = any(indicator in text_lower for indicator in question_indicators)
        
        if self.chatgpt_enabled and (is_question or len(text.split()) > 3):
            # This looks like a question for ChatGPT
            self.logger.info(f"ChatGPT question detected: {text}")
            self._process_chatgpt_question(text)
        else:
            # Unknown command
            self.logger.info(f"Unknown command: {text}")
            self._speak("I didn't understand that command. Say 'Bible Clock help' to learn about all available commands.")
    
    def _handle_help_commands(self, text: str) -> bool:
        """Handle help-related commands."""
        if not self.help_enabled:
            return False
        
        help_commands = {
            'help': self._speak_general_help,
            'help me': self._speak_general_help,
            'commands': self._speak_general_help,
            'what can you do': self._speak_general_help,
            'help display': self._speak_display_help,
            'help information': self._speak_information_help,
            'help questions': self._speak_chatgpt_help,
            'help examples': self._speak_chatgpt_examples,
            'help setup': self._speak_setup_help
        }
        
        for help_cmd, help_action in help_commands.items():
            if help_cmd in text:
                self.logger.info(f"Help command executed: {help_cmd}")
                help_action()
                return True
        
        return False
    
    def _speak_general_help(self):
        """Speak the general help overview."""
        help_data = self.help_commands["overview"]
        self._speak(help_data["content"])
        time.sleep(self.help_section_pause)
        
        # Provide overview of categories
        categories = [
            "Display control commands for changing backgrounds and modes",
            "Information commands for system status and current settings",
            "Biblical questions using artificial intelligence",
            "Help commands for detailed assistance"
        ]
        
        self._speak("I can help you with four main categories:")
        for i, category in enumerate(categories, 1):
            self._speak(f"{i}. {category}")
            time.sleep(1)
        
        time.sleep(self.help_section_pause)
        self._speak("Say 'Bible Clock help' followed by a category name for detailed information. "
                   "For example, 'Bible Clock help display' or 'Bible Clock help questions'.")
    
    def _speak_display_help(self):
        """Speak display control help."""
        help_data = self.help_commands["display_commands"]
        self._speak(help_data["title"])
        time.sleep(self.help_section_pause)
        
        for command, description in help_data["commands"].items():
            self._speak(f"Say 'Bible Clock {command}' and {description}")
            time.sleep(1)
    
    def _speak_information_help(self):
        """Speak information commands help."""
        help_data = self.help_commands["information_commands"]
        self._speak(help_data["title"])
        time.sleep(self.help_section_pause)
        
        for command, description in help_data["commands"].items():
            self._speak(f"Say 'Bible Clock {command}' and {description}")
            time.sleep(1)
    
    def _speak_chatgpt_help(self):
        """Speak ChatGPT capabilities help."""
        if not self.chatgpt_enabled:
            self._speak("Biblical questions are not currently enabled. Please check your configuration to enable the AI assistant.")
            return
        
        help_data = self.help_commands["chatgpt_commands"]
        self._speak(help_data["title"])
        time.sleep(self.help_section_pause)
        self._speak(help_data["content"])
        time.sleep(self.help_section_pause)
        
        self._speak("Here are some example questions you can ask:")
        for example in help_data["examples"][:5]:  # First 5 examples
            self._speak(f"Bible Clock, {example}")
            time.sleep(1)
        
        time.sleep(self.help_section_pause)
        self._speak("I understand the current verse being displayed and can provide context-aware explanations.")
    
    def _speak_chatgpt_examples(self):
        """Speak more ChatGPT examples."""
        if not self.chatgpt_enabled:
            self._speak("Biblical questions are not currently enabled.")
            return
        
        help_data = self.help_commands["chatgpt_commands"]
        self._speak("Here are more examples of biblical questions you can ask:")
        
        for example in help_data["examples"]:
            self._speak(f"Bible Clock, {example}")
            time.sleep(1)
    
    def _speak_setup_help(self):
        """Speak setup and configuration help."""
        help_data = self.help_commands["setup_help"]
        self._speak(help_data["title"])
        time.sleep(self.help_section_pause)
        self._speak(help_data["content"])
    
    def _process_chatgpt_question(self, question: str):
        """Process question using ChatGPT."""
        if not self.chatgpt_enabled:
            self._speak("Biblical questions are not currently enabled. Please check your configuration to enable the AI assistant.")
            return
        
        start_time = time.time()
        
        try:
            import openai
            
            self._speak("Let me think about that for you...")
            
            # Prepare context with current verse
            context_info = ""
            if self.current_verse_context:
                context_info = f"\n\nCurrent verse being displayed: {self.current_verse_context['reference']} - \"{self.current_verse_context['text']}\""
                if self.current_verse_context.get('is_date_event'):
                    context_info += f"\nThis is displayed as part of: {self.current_verse_context.get('event_name', 'a biblical calendar event')}"
                if self.current_verse_context.get('is_summary'):
                    context_info += f"\nThis is a book summary for the book of {self.current_verse_context.get('book', 'the Bible')}"
            
            # Prepare conversation with context
            messages = [
                {"role": "system", "content": self.system_prompt + context_info}
            ]
            
            # Add recent conversation history (last 4 exchanges)
            messages.extend(self.conversation_history[-8:])
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            # Call ChatGPT API
            response = openai.ChatCompletion.create(
                model=self.chatgpt_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.chatgpt_timeout
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Extract token usage
            token_usage = response.get('usage', {})
            total_tokens = token_usage.get('total_tokens', 0)
            prompt_tokens = token_usage.get('prompt_tokens', 0)
            completion_tokens = token_usage.get('completion_tokens', 0)
            
            # Update token usage statistics
            self._update_token_stats(total_tokens, response_time, True)
            
            answer = response.choices[0].message.content.strip()
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            # Keep only recent history to manage token usage
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            self.logger.info(f"ChatGPT response generated for: {question} (Tokens: {total_tokens}, Time: {response_time:.1f}s)")
            
            # Speak the response
            self._speak(answer)
            
            # Log the interaction with token info
            self._log_chatgpt_interaction(question, answer, {
                'tokens': total_tokens,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'response_time': response_time
            })
            
        except Exception as e:
            # Update failed request stats
            response_time = time.time() - start_time
            self._update_token_stats(0, response_time, False)
            
            self.logger.error(f"ChatGPT processing error: {e}")
            self._speak("I'm sorry, I'm having trouble accessing my biblical knowledge base right now. Please try again later.")
    
    def _update_token_stats(self, tokens: int, response_time: float, success: bool):
        """Update token usage statistics."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if success:
            self.token_usage_stats['total_tokens'] += tokens
            self.token_usage_stats['total_questions'] += 1
            self.token_usage_stats['successful_requests'] += 1
            
            # Estimate cost (GPT-3.5-turbo: ~$0.002 per 1K tokens)
            cost_per_1k_tokens = 0.002
            self.token_usage_stats['total_cost'] += (tokens / 1000) * cost_per_1k_tokens
        else:
            self.token_usage_stats['failed_requests'] += 1
        
        # Track response times (keep last 100 for average calculation)
        self.token_usage_stats['response_times'].append(response_time)
        if len(self.token_usage_stats['response_times']) > 100:
            self.token_usage_stats['response_times'] = self.token_usage_stats['response_times'][-100:]
        
        # Track daily usage
        if today not in self.token_usage_stats['daily_usage']:
            self.token_usage_stats['daily_usage'][today] = {'tokens': 0, 'questions': 0}
        
        if success:
            self.token_usage_stats['daily_usage'][today]['tokens'] += tokens
            self.token_usage_stats['daily_usage'][today]['questions'] += 1
    
    def _log_chatgpt_interaction(self, question: str, answer: str, usage_info: dict = None):
        """Log ChatGPT interactions for review."""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'question': question,
                'answer': answer,
                'verse_context': self.current_verse_context.get('reference') if self.current_verse_context else None
            }
            
            # Add usage information if provided
            if usage_info:
                log_entry['usage'] = usage_info
            
            # Append to interactions log file
            log_file = 'logs/chatgpt_interactions.jsonl'
            os.makedirs('logs', exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error logging ChatGPT interaction: {e}")
    
    # Enhanced built-in commands
    def _speak_current_verse(self):
        """Speak the current verse aloud."""
        try:
            verse_data = self.verse_manager.get_current_verse()
            
            if verse_data.get('is_summary'):
                text_to_speak = f"Here is a summary for the book of {verse_data['book']}. {verse_data['text']}"
            elif verse_data.get('is_date_event'):
                text_to_speak = f"Today's biblical event is {verse_data.get('event_name', 'a biblical event')}. From {verse_data['reference']}: {verse_data['text']}"
            else:
                text_to_speak = f"The current verse is {verse_data['reference']}: {verse_data['text']}"
            
            self._speak(text_to_speak)
            
        except Exception as e:
            self.logger.error(f"Error speaking verse: {e}")
            self._speak("Sorry, I couldn't read the current verse.")
    
    def _speak_current_verse_info(self):
        """Speak information about the current verse."""
        try:
            verse_data = self.verse_manager.get_current_verse()
            
            if verse_data.get('is_summary'):
                info = f"Currently displaying a summary for the book of {verse_data['book']}"
            elif verse_data.get('is_date_event'):
                info = f"Currently displaying {verse_data.get('event_name', 'a biblical event')} from {verse_data['reference']}"
            else:
                info = f"Currently displaying {verse_data['reference']} from the book of {verse_data.get('book', 'the Bible')}"
            
            # Add mode information
            current_mode = getattr(self.verse_manager, 'display_mode', 'time')
            translation = getattr(self.verse_manager, 'translation', 'KJV')
            
            info += f". We are in {current_mode} mode using the {translation.upper()} translation."
            
            self._speak(info)
            
        except Exception as e:
            self.logger.error(f"Error getting verse info: {e}")
            self._speak("Sorry, I couldn't get information about the current verse.")
    
    def _speak_current_mode(self):
        """Speak the current display mode."""
        try:
            current_mode = getattr(self.verse_manager, 'display_mode', 'time')
            mode_descriptions = {
                'time': 'time-based mode, where the hour determines the chapter and minute determines the verse',
                'date': 'date-based mode, showing biblical calendar events and seasonal themes',
                'random': 'random mode, displaying inspirational verses for meditation'
            }
            
            description = mode_descriptions.get(current_mode, current_mode)
            self._speak(f"We are currently in {description}.")
            
        except Exception as e:
            self.logger.error(f"Error getting current mode: {e}")
            self._speak("Sorry, I couldn't determine the current display mode.")
    
    def _speak_current_translation(self):
        """Speak the current Bible translation."""
        try:
            translation = getattr(self.verse_manager, 'translation', 'KJV')
            translation_names = {
                'kjv': 'King James Version',
                'esv': 'English Standard Version',
                'nasb': 'New American Standard Bible',
                'amp': 'Amplified Bible',
                'niv': 'New International Version'
            }
            
            full_name = translation_names.get(translation.lower(), translation.upper())
            self._speak(f"We are currently using the {full_name} translation.")
            
        except Exception as e:
            self.logger.error(f"Error getting current translation: {e}")
            self._speak("Sorry, I couldn't determine the current Bible translation.")
    
    def _cycle_translation(self):
        """Cycle through Bible translations."""
        current_translation = getattr(self.verse_manager, 'translation', 'kjv')
        translations = self.verse_manager.get_available_translations()
        translation_names = {
            'kjv': 'King James Version',
            'web': 'World English Bible',
            'asv': 'American Standard Version',
            'bbe': 'Bible in Basic English',
            'ylt': 'Young\'s Literal Translation',
            'darby': 'Darby Bible',
            'esv': 'English Standard Version',
            'amp': 'Amplified Bible',
            'nasb': 'New American Standard Bible',
            'cev': 'Contemporary English Version'
        }
        
        try:
            current_index = translations.index(current_translation.lower())
            next_index = (current_index + 1) % len(translations)
            next_translation = translations[next_index]
            
            self.verse_manager.translation = next_translation
            
            full_name = translation_names.get(next_translation, next_translation.upper())
            self._speak(f"Switched to the {full_name}")
            self.logger.info(f"Translation changed to: {next_translation}")
            
            # Update display with new translation
            self._refresh_display()
            
        except (ValueError, AttributeError):
            self.logger.warning(f"Unknown translation: {current_translation}")
            self._speak("Bible translation has been changed.")
    
    def _cycle_display_mode(self):
        """Cycle through display modes."""
        current_mode = getattr(self.verse_manager, 'display_mode', 'time')
        modes = ['time', 'date', 'random']
        mode_descriptions = {
            'time': 'time-based mode where hour equals chapter and minute equals verse',
            'date': 'date-based mode showing biblical calendar events',
            'random': 'random mode for inspirational verses'
        }
        
        try:
            current_index = modes.index(current_mode)
            next_index = (current_index + 1) % len(modes)
            next_mode = modes[next_index]
            
            self.verse_manager.display_mode = next_mode
            
            description = mode_descriptions[next_mode]
            self._speak(f"Switched to {description}")
            self.logger.info(f"Display mode changed to: {next_mode}")
            
            # Update display with new mode
            self._refresh_display()
            
        except (ValueError, AttributeError):
            self._speak("Display mode has been changed.")
    
    def _set_display_mode(self, mode: str):
        """Set specific display mode."""
        mode_descriptions = {
            'time': 'time-based mode where hour equals chapter and minute equals verse',
            'date': 'date-based mode showing biblical calendar events',
            'random': 'random mode for inspirational verses'
        }
        
        try:
            self.verse_manager.display_mode = mode
            description = mode_descriptions.get(mode, mode)
            self._speak(f"Switched to {description}")
            self.logger.info(f"Display mode set to: {mode}")
            
            # Update display with new mode
            self._refresh_display()
            
        except Exception as e:
            self.logger.error(f"Error setting display mode: {e}")
            self._speak(f"Sorry, I couldn't switch to {mode} mode.")
    
    def _change_background(self):
        """Change background image."""
        try:
            self.image_generator.cycle_background()
            bg_info = self.image_generator.get_current_background_info()
            
            self._speak(f"Background changed to style {bg_info['current_index'] + 1} of {bg_info['total_backgrounds']}")
            
            # Update display with new background
            self._refresh_display()
            
        except Exception as e:
            self.logger.error(f"Error changing background: {e}")
            self._speak("Sorry, I couldn't change the background.")
    
    def _speak_time(self):
        """Speak the current time."""
        try:
            now = datetime.now()
            # Format time with leading zeros for hours
            hour_12 = now.hour % 12
            if hour_12 == 0:
                hour_12 = 12
            time_str = f"It is {hour_12:02d}:{now.minute:02d} {now.strftime('%p on %A, %B %d')}"
            self._speak(time_str)
        except Exception as e:
            self.logger.error(f"Error getting time: {e}")
            self._speak("Sorry, I couldn't get the current time.")
    
    def _speak_system_status(self):
        """Speak system status information."""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Determine status description
            if cpu_percent < 50 and memory_percent < 70:
                status_desc = "excellent"
            elif cpu_percent < 70 and memory_percent < 80:
                status_desc = "good"
            else:
                status_desc = "moderate"
            
            status_text = f"System status is {status_desc}. CPU usage is {cpu_percent:.0f} percent. Memory usage is {memory_percent:.0f} percent."
            
            # Add current settings information
            current_mode = getattr(self.verse_manager, 'display_mode', 'time')
            translation = getattr(self.verse_manager, 'translation', 'KJV')
            status_text += f" Currently in {current_mode} mode using {translation.upper()} translation."
            
            self._speak(status_text)
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            self._speak("System is running normally.")
    
    def _refresh_display(self):
        """Refresh the display with current verse."""
        try:
            verse_data = self.verse_manager.get_current_verse()
            image = self.image_generator.create_verse_image(verse_data)
            self.display_manager.display_image(image, force_refresh=True)
            
            self._speak("Display has been refreshed")
            
        except Exception as e:
            self.logger.error(f"Error refreshing display: {e}")
            self._speak("Sorry, I couldn't refresh the display.")
    
    def _clear_display(self):
        """Clear the display."""
        try:
            self.display_manager.clear_display()
            self._speak("Display has been cleared")
        except Exception as e:
            self.logger.error(f"Error clearing display: {e}")
            self._speak("Sorry, I couldn't clear the display.")
    
    def _speak(self, text: str):
        """Speak text using TTS with enhanced voice settings and display management."""
        # Check if screen display is enabled instead of audio output
        if self.screen_display_enabled:
            self._display_response_on_screen(text)
            return
        
        # Check if audio output is enabled
        if not self.audio_output_enabled:
            self.logger.debug(f"Audio output disabled - would speak: {text[:100]}{'...' if len(text) > 100 else ''}")
            return
            
        if not self.tts_engine:
            self.logger.warning(f"TTS not available - would speak: {text[:100]}{'...' if len(text) > 100 else ''}")
            return
        
        try:
            # Log what's being spoken (truncated for readability)
            self.logger.info(f"Speaking: {text[:100]}{'...' if len(text) > 100 else ''}")
            
            # Show speaking status on display with auto-timeout
            if hasattr(self.display_manager, 'show_transient_message'):
                self.display_manager.show_transient_message("speaking", duration=5.0)  # Auto-clear after 5 seconds
            
            # Enhance speech for better clarity
            enhanced_text = self._enhance_speech_text(text)
            
            # Configure audio output device (USB audio preferred, ReSpeaker legacy)
            if self.usb_audio_enabled and self.audio_output_enabled:
                # USB audio devices - use default TTS output (should route to USB speakers)
                self.logger.debug("Using USB audio output for TTS")
                self.tts_engine.say(enhanced_text)
                self.tts_engine.runAndWait()
            elif self.respeaker_enabled and self.force_respeaker_output:
                # Legacy ReSpeaker support
                original_pulse_device = os.environ.get('PULSE_PCM_DEVICE')
                os.environ['PULSE_PCM_DEVICE'] = 'hw:seeedvoicecard,0'
                try:
                    self.tts_engine.say(enhanced_text)
                    self.tts_engine.runAndWait()
                finally:
                    # Restore original device setting
                    if original_pulse_device:
                        os.environ['PULSE_PCM_DEVICE'] = original_pulse_device
                    elif 'PULSE_PCM_DEVICE' in os.environ:
                        del os.environ['PULSE_PCM_DEVICE']
            else:
                # Default audio output
                self.tts_engine.say(enhanced_text)
                self.tts_engine.runAndWait()
            
            # Restore normal display after speaking completes
            self._restore_display_after_speech()
            
            # Start a backup timer to ensure display restoration
            self._start_display_restore_timer()
            
        except Exception as e:
            self.logger.error(f"TTS error: {e}")
            self.logger.warning(f"Failed to speak: {text[:100]}{'...' if len(text) > 100 else ''}")
            # Still try to restore display even if speech failed
            self._restore_display_after_speech()
        finally:
            # Ensure display restoration happens even if there are unexpected errors
            try:
                # Add a small delay to ensure any ongoing operations complete
                import time
                time.sleep(0.5)
                # Force display restoration if not already done
                if hasattr(self.display_manager, 'show_transient_message'):
                    # Clear any transient message by showing the normal display
                    self._refresh_display_silent()
            except Exception as restore_error:
                self.logger.error(f"Final display restoration failed: {restore_error}")
    
    def _display_response_on_screen(self, text: str, duration: float = 15.0):
        """Display AI response on e-ink screen instead of speaking."""
        try:
            self.logger.info(f"Displaying response on screen: {text[:100]}{'...' if len(text) > 100 else ''}")
            
            # Use the display manager's transient message system
            if hasattr(self.display_manager, 'show_transient_message'):
                self.display_manager.show_transient_message("ai_response", text, duration)
            else:
                # Fallback: log the text if display manager not available
                self.logger.warning("Display manager not available for screen response")
                self.logger.info(f"AI Response: {text}")
                
        except Exception as e:
            self.logger.error(f"Error displaying response on screen: {e}")
            # Don't fallback to speaking here to avoid infinite loops
            # Just log the response
            self.logger.info(f"Failed to display - AI Response: {text}")
    
    def _enhance_speech_text(self, text: str) -> str:
        """Enhance text for better speech synthesis."""
        # Add pauses for better comprehension
        enhanced = text.replace('. ', '. ')
        enhanced = enhanced.replace('? ', '? ')
        enhanced = enhanced.replace('! ', '! ')
        
        # Improve pronunciation of common biblical terms
        biblical_pronunciations = {
            'KJV': 'K. J. V.',
            'ESV': 'E. S. V.',
            'NASB': 'N. A. S. B.',
            'AMP': 'A. M. P.',
            'NIV': 'N. I. V.',
            'vs.': 'verses',
            'v.': 'verse'
        }
        
        for term, pronunciation in biblical_pronunciations.items():
            enhanced = enhanced.replace(term, pronunciation)
        
        return enhanced
    
    # Utility methods for external control
    def clear_conversation_history(self):
        """Clear ChatGPT conversation history."""
        self.conversation_history = []
        self.logger.info("Conversation history cleared")
    
    def get_conversation_history(self) -> list:
        """Get current conversation history."""
        return self.conversation_history.copy()
    
    def set_chatgpt_enabled(self, enabled: bool):
        """Enable or disable ChatGPT integration."""
        if enabled and not self.openai_api_key:
            self.logger.warning("Cannot enable ChatGPT without API key")
            return False
        
        self.chatgpt_enabled = enabled
        self.logger.info(f"ChatGPT integration {'enabled' if enabled else 'disabled'}")
        return True
    
    def test_voice_synthesis(self, test_text: str = None):
        """Test voice synthesis with a sample phrase."""
        if test_text is None:
            test_text = "Hello! Bible Clock voice control is working properly. I can help you with display control, system information, and biblical questions."
        
        self._speak(test_text)
    
    def get_voice_status(self) -> Dict[str, Any]:
        """Get comprehensive voice control status."""
        return {
            'enabled': self.enabled,
            'listening': self.listening,
            'wake_word': self.wake_word,
            'chatgpt_enabled': self.chatgpt_enabled,
            'help_enabled': self.help_enabled,
            'respeaker_enabled': self.respeaker_enabled,
            'voice_rate': self.voice_rate,
            'voice_volume': self.voice_volume,
            'voice_selection': getattr(self, 'voice_selection', 'default'),
            'conversation_length': len(self.conversation_history),
            'available_commands': list(self.help_commands.keys()),
            'chatgpt_api_key': bool(self.openai_api_key),  # Just show if key is set
            # Audio input/output controls
            'audio_input_enabled': self.audio_input_enabled,
            'audio_output_enabled': self.audio_output_enabled,
            'screen_display_enabled': self.screen_display_enabled,
            'force_respeaker_output': self.force_respeaker_output,
            # ReSpeaker settings
            'respeaker_channels': self.respeaker_channels,
            'respeaker_sample_rate': self.respeaker_sample_rate,
            'respeaker_chunk_size': self.respeaker_chunk_size,
            # Additional voice settings
            'voice_timeout': self.voice_timeout,
            'phrase_limit': self.phrase_limit,
            'help_section_pause': self.help_section_pause
        }
    
    def get_ai_statistics(self) -> Dict[str, Any]:
        """Get AI/ChatGPT usage statistics."""
        stats = self.token_usage_stats.copy()
        
        # Calculate success rate
        total_requests = stats['successful_requests'] + stats['failed_requests']
        if total_requests > 0:
            success_rate = (stats['successful_requests'] / total_requests) * 100
        else:
            success_rate = 0
        
        # Calculate average response time
        if stats['response_times']:
            avg_response_time = sum(stats['response_times']) / len(stats['response_times'])
        else:
            avg_response_time = 0
        
        return {
            'total_tokens': stats['total_tokens'],
            'total_questions': stats['total_questions'],
            'total_cost': stats['total_cost'],
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'successful_requests': stats['successful_requests'],
            'failed_requests': stats['failed_requests'],
            'daily_usage': stats['daily_usage']
        }
    
    def _handle_translation_change_command(self, text: str) -> bool:
        """Handle 'change translation to X' commands."""
        if 'change translation to' not in text:
            return False
        
        # Extract the translation name
        parts = text.split('change translation to')
        if len(parts) != 2:
            return False
        
        translation_name = parts[1].strip()
        
        # Map spoken names to translation codes
        translation_map = {
            'king james': 'kjv',
            'kjv': 'kjv',
            'king james version': 'kjv',
            'world english bible': 'web',
            'web': 'web',
            'american standard': 'asv',
            'asv': 'asv',
            'american standard version': 'asv',
            'bible in basic english': 'bbe',
            'bbe': 'bbe',
            'basic english': 'bbe',
            'youngs literal': 'ylt',
            'ylt': 'ylt',
            'youngs literal translation': 'ylt',
            'darby': 'darby',
            'darby bible': 'darby',
            'english standard': 'esv',
            'esv': 'esv',
            'english standard version': 'esv',
            'amplified': 'amp',
            'amp': 'amp',
            'amplified bible': 'amp',
            'new american standard': 'nasb',
            'nasb': 'nasb',
            'new american standard bible': 'nasb',
            'contemporary english': 'cev',
            'cev': 'cev',
            'contemporary english version': 'cev'
        }
        
        translation_code = translation_map.get(translation_name.lower())
        if not translation_code:
            self._speak(f"I don't recognize the translation '{translation_name}'. Available translations include King James, Web, American Standard, English Standard, Amplified, New American Standard, and Contemporary English versions.")
            return True
        
        # Check if translation is available
        available_translations = self.verse_manager.get_available_translations()
        if translation_code not in available_translations:
            self._speak(f"The {translation_name} translation is not currently available.")
            return True
        
        # Set the translation
        try:
            old_translation = self.verse_manager.translation
            self.verse_manager.translation = translation_code
            
            # Get translation display name
            display_names = {
                'kjv': 'King James Version',
                'web': 'World English Bible',
                'asv': 'American Standard Version',
                'bbe': 'Bible in Basic English',
                'ylt': 'Young\'s Literal Translation',
                'darby': 'Darby Bible',
                'esv': 'English Standard Version',
                'amp': 'Amplified Bible',
                'nasb': 'New American Standard Bible',
                'cev': 'Contemporary English Version'
            }
            
            display_name = display_names.get(translation_code, translation_code.upper())
            self._speak(f"Translation changed to {display_name}")
            
            # Update display
            self._refresh_display()
            
            self.logger.info(f"Translation changed from {old_translation} to {translation_code}")
            
        except Exception as e:
            self.logger.error(f"Error changing translation: {e}")
            self._speak("Sorry, I couldn't change the translation. Please try again.")
        
        return True
    
    def _handle_change_mode_command(self):
        """Enhanced change mode command with parallel mode support."""
        self._speak("What mode would you like? Say time mode, date mode, random mode, or parallel mode.")
        
        # Wait for response
        try:
            response = self._listen_for_response(timeout=8)
            if response:
                response_lower = response.lower()
                
                if 'time' in response_lower:
                    self._set_display_mode('time')
                elif 'date' in response_lower:
                    self._set_display_mode('date')
                elif 'random' in response_lower:
                    self._set_display_mode('random')
                elif 'parallel' in response_lower:
                    self._toggle_parallel_mode()
                else:
                    self._speak("I didn't understand. Using the cycling mode instead.")
                    self._cycle_display_mode()
            else:
                self._speak("No response received. Using the cycling mode instead.")
                self._cycle_display_mode()
                
        except Exception as e:
            self.logger.error(f"Error in change mode command: {e}")
            self._cycle_display_mode()
    
    def _toggle_parallel_mode(self):
        """Toggle parallel translation mode."""
        try:
            current_parallel = getattr(self.verse_manager, 'parallel_mode', False)
            self.verse_manager.parallel_mode = not current_parallel
            
            if self.verse_manager.parallel_mode:
                primary = self.verse_manager.translation.upper()
                secondary = getattr(self.verse_manager, 'secondary_translation', 'amp').upper()
                self._speak(f"Parallel mode enabled. Showing {primary} and {secondary} translations side by side.")
            else:
                self._speak("Parallel mode disabled. Showing single translation.")
            
            # Update display
            self._refresh_display()
            
            self.logger.info(f"Parallel mode {'enabled' if self.verse_manager.parallel_mode else 'disabled'}")
            
        except Exception as e:
            self.logger.error(f"Error toggling parallel mode: {e}")
            self._speak("Sorry, I couldn't toggle parallel mode.")
    
    def _start_chat_mode(self):
        """Start interactive chat mode with ChatGPT - supports continuous conversation."""
        if not self.chatgpt_enabled:
            self._speak("Chat mode is not currently enabled. Please check your Chat GPT configuration.")
            return
        
        self._speak("Chat mode activated. Ask me biblical questions. Say 'stop chat' to end.")
        
        # Continuous chat loop
        chat_active = True
        questions_asked = 0
        max_questions = 10  # Prevent infinite loops
        
        while chat_active and questions_asked < max_questions:
            try:
                self.logger.info(f"Chat mode: Listening for question {questions_asked + 1}")
                
                # Listen for user question
                response = self._listen_for_response(timeout=20)
                
                if not response:
                    self._speak("I didn't hear anything. Chat mode ended.")
                    break
                
                response_lower = response.lower().strip()
                
                # Check for exit commands
                exit_commands = ['stop chat', 'exit chat', 'end chat', 'stop', 'exit', 'quit chat']
                if any(cmd in response_lower for cmd in exit_commands):
                    self._speak("Chat mode ended. Returning to Bible Clock.")
                    break
                
                # Process the question
                self.logger.info(f"Chat mode: Processing question: {response}")
                self._process_chatgpt_question(response)
                questions_asked += 1
                
                # After answering, prompt for next question
                if questions_asked < max_questions:
                    # Small delay to ensure display restoration completes
                    import time
                    time.sleep(1)
                    self._speak("Do you have another question? Or say 'stop chat' to end.")
                else:
                    self._speak("That's enough questions for now. Chat mode ended.")
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in chat mode loop: {e}")
                self._speak("Sorry, there was an error. Chat mode ended.")
                break
        
        # Ensure display is restored when chat ends
        self.logger.info("Chat mode ended, restoring display")
        self._restore_display_after_speech()
    
    def _listen_for_response(self, timeout: int = 10) -> Optional[str]:
        """Listen for a voice response with timeout."""
        if not self.recognizer or not self.microphone:
            return None
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=self.phrase_limit)
            
            text = self.recognizer.recognize_google(audio)
            self.logger.info(f"Voice response received: {text}")
            return text
            
        except Exception as e:
            self.logger.debug(f"Voice response timeout or error: {e}")
            return None
    
    def _restore_display_after_speech(self):
        """Restore normal Bible Clock display after speech completes."""
        try:
            # Use the display manager's restore callback if available
            if hasattr(self.display_manager, 'restore_callback') and self.display_manager.restore_callback:
                self.logger.info("Restoring display after speech using callback")
                self.display_manager.restore_callback()
            else:
                # Fallback: trigger a silent display refresh to show current verse
                self.logger.info("Restoring display after speech using silent refresh")
                self._refresh_display_silent()
                
        except Exception as e:
            self.logger.error(f"Error restoring display after speech: {e}")
    
    def _refresh_display_silent(self):
        """Silently refresh the display without speaking."""
        try:
            verse_data = self.verse_manager.get_current_verse()
            image = self.image_generator.create_verse_image(verse_data)
            self.display_manager.display_image(image, force_refresh=True)
            self.logger.info("Display silently refreshed after speech")
            
        except Exception as e:
            self.logger.error(f"Error in silent display refresh: {e}")
    
    def _force_display_restore(self):
        """Force display restoration and clear any stuck status."""
        try:
            self.logger.info("Force display restore requested")
            
            # Clear any transient messages
            if hasattr(self.display_manager, 'show_transient_message'):
                self.display_manager.show_transient_message("ready", duration=0.5)
            
            # Restore normal display
            self._refresh_display_silent()
            
            self._speak("Display restored to Bible Clock.")
            
        except Exception as e:
            self.logger.error(f"Error in force display restore: {e}")
            # Try a basic clear as last resort
            try:
                if hasattr(self.display_manager, 'clear_display'):
                    self.display_manager.clear_display()
            except:
                pass
    
    def _start_display_restore_timer(self):
        """Start a backup timer to ensure display gets restored."""
        def restore_after_delay():
            import time
            time.sleep(8)  # Wait 8 seconds then force restore
            try:
                self.logger.info("Backup display restore timer triggered")
                self._refresh_display_silent()
            except Exception as e:
                self.logger.error(f"Backup display restore failed: {e}")
        
        # Start timer in background thread
        import threading
        timer_thread = threading.Thread(target=restore_after_delay, daemon=True)
        timer_thread.start()


# Backward compatibility alias
VoiceControl = BibleClockVoiceControl