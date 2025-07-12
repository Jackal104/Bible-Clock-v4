#!/usr/bin/env python3
"""
Voice Assistant Module for Bible Clock
Professional voice interaction with interrupt handling, VAD, and performance metrics
"""

import os
import sys
import logging
import speech_recognition as sr
from src.conversation_manager import ConversationManager
import time as time_module
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
import threading
import queue
import contextlib

# Suppress ALSA error messages - minimal approach
os.environ['ALSA_QUIET'] = '1'
os.environ['JACK_NO_START_SERVER'] = '1'

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class VoiceAssistant:
    """Professional voice assistant with wake word detection, VAD, and streaming responses."""
    
    def __init__(self, verse_manager=None, visual_feedback_callback=None):
        """Initialize the voice assistant.
        
        Args:
            verse_manager: Optional verse manager for Bible context
            visual_feedback_callback: Function to call for visual state updates
        """
        self._enabled = os.getenv('ENABLE_CHATGPT_VOICE', 'true').lower() == 'true'
        self.voice_timeout = int(os.getenv('VOICE_TIMEOUT', '10'))
        
        # Audio device configuration
        self.usb_speaker_device = 'plughw:2,0'
        self.usb_mic_device = 'plughw:1,0'
        
        # API configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '').replace('\n', '').replace('\r', '').replace(' ', '')
        self.chatgpt_model = os.getenv('CHATGPT_MODEL', 'gpt-3.5-turbo')
        
        # TTS configuration from environment variables
        self.tts_engine = os.getenv('TTS_ENGINE', 'openai')
        self.tts_model = os.getenv('TTS_MODEL', 'tts-1')
        self.tts_voice = os.getenv('TTS_VOICE', 'nova')
        self.tts_audio_format = os.getenv('TTS_AUDIO_FORMAT', 'wav')
        self.tts_streaming = os.getenv('TTS_STREAMING', 'true').lower() == 'true'
        self.allow_piper_fallback = os.getenv('ALLOW_PIPER_FALLBACK', 'true').lower() == 'true'
        
        # Memory optimization settings
        self.MAX_TTS_QUEUE_SIZE = 2  # Limit TTS queue to prevent memory growth
        self.MAX_AUDIO_BUFFER_SIZE = 3  # Limit audio buffer accumulation
        self.max_tokens = int(os.getenv('CHATGPT_MAX_TOKENS', '50'))
        self.system_prompt = os.getenv('CHATGPT_SYSTEM_PROMPT', 
            'You are a knowledgeable Bible study assistant. Provide accurate, thoughtful responses about the Bible, Christianity, and faith. Keep responses VERY brief (1-2 sentences max, under 50 words) for voice assistant use. Be concise and direct.')
        
        # Porcupine access key
        self.porcupine_access_key = os.getenv('PICOVOICE_ACCESS_KEY', '')
        
        # Wake word configuration
        self.wake_word = 'Bible Clock'
        
        # Piper TTS configuration
        self.piper_model_path = os.path.expanduser('~/.local/share/piper/voices/en_US-amy-medium.onnx')
        
        # Voice components
        self.verse_manager = verse_manager
        self.recognizer = None
        
        # Conversation management and metrics
        self.conversation_manager = ConversationManager()
        
        # Timing metrics for performance tracking
        self.timing_metrics = {
            'speech_recognition_time': 0.0,
            'chatgpt_processing_time': 0.0,
            'tts_generation_time': 0.0
        }
        self.openai_client = None
        self.porcupine = None
        self.pyaudio = None
        self.usb_mic_index = None
        self.mic_sample_rate = None
        
        # Visual feedback
        self.visual_feedback = visual_feedback_callback
        
        # Voice control state management
        self.listening = self.enabled  # Start listening if voice control is enabled
        self.should_stop = False  # Controls main loop termination
        
        # TTS queue for preventing overlapping speech
        self.tts_queue = queue.Queue()
        self.tts_thread = None
        self.tts_thread_running = False
        self.tts_interrupt_event = threading.Event()
        
        # Performance metrics
        self.metrics = {
            'wake_word_time': None,
            'command_start_time': None,
            'command_end_time': None,
            'gpt_start_time': None,
            'gpt_first_response_time': None,
            'first_speech_time': None
        }
        
        # Interrupt detection
        self.interrupt_detection_active = False
        self.interrupt_thread = None
        
        # Audio device lock to prevent simultaneous access
        self.audio_lock = threading.Lock()
        
        if self.enabled:
            self._initialize_components()
        
        # Mark as initialized for property setter visual feedback
        self._initialized = True
    
    def _update_visual_state(self, state, message=None):
        """Update visual feedback if callback is provided."""
        if self.visual_feedback:
            try:
                self.visual_feedback(state, message)
            except Exception as e:
                logger.warning(f"Visual feedback error: {e}")
        else:
            logger.warning("❌ No visual feedback callback available")
    
    def _restore_display_after_tts(self):
        """Restore display to normal after TTS completion."""
        def delayed_restore():
            try:
                # Wait a moment to ensure TTS has fully completed
                time_module.sleep(1.0)
                logger.info("🔄 Restoring display after TTS completion")
                self._update_visual_state("ready", "✅ Ready")
                # Additional delay then clear the ready message
                time_module.sleep(2.0)
                # Trigger full display restoration to Bible verse
                logger.info("🔄 Triggering final display restoration to Bible verse")
                if self.visual_feedback:
                    self.visual_feedback("restore", None)
                else:
                    logger.warning("No visual feedback callback available for restoration")
            except Exception as e:
                logger.error(f"Display restoration failed: {e}")
        
        # Run restoration in background thread
        import threading
        threading.Thread(target=delayed_restore, daemon=True).start()
    
    def _initialize_components(self):
        """Initialize all voice control components with error handling."""
        try:
            self._update_visual_state("initializing", "Starting voice system...")
            
            # Initialize speech recognition
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.recognizer.operation_timeout = self.voice_timeout
            logger.info("Speech recognizer initialized")
            
            logger.info(f"Wake word detection ready for '{self.wake_word}'")
            
            # Test Piper TTS
            if not Path(self.piper_model_path).exists():
                logger.error(f"Amy voice model not found: {self.piper_model_path}")
                return False
            
            # Initialize Porcupine for wake word detection
            self._initialize_porcupine()
            
            # Initialize OpenAI client (modern API)
            if self.openai_api_key:
                self._initialize_openai_client()
                logger.info("OpenAI client initialized with modern API")
            else:
                logger.warning("No OpenAI API key configured")
            
            logger.info("All voice components initialized successfully")
            self._update_visual_state("ready", "Voice assistant ready")
            return True
            
        except Exception as e:
            logger.error(f"Voice system initialization failed: {e}")
            self.enabled = False
            self._update_visual_state("error", f"Init failed: {str(e)}")
            return False
    
    def _initialize_porcupine(self):
        """Initialize Porcupine wake word detection with custom Bible Clock wake word."""
        try:
            import pvporcupine
            import pyaudio
            
            # Path to custom Bible Clock wake word file
            bible_clock_ppn = Path('./Bible-Clock_en_raspberry-pi_v3_0_0.ppn')
            
            if not bible_clock_ppn.exists():
                logger.error(f"Custom Bible Clock wake word file not found: {bible_clock_ppn}")
                return False
            
            # Explicit access key validation
            access_key = os.getenv("PICOVOICE_ACCESS_KEY")
            if not access_key:
                logger.error("Missing PICOVOICE_ACCESS_KEY in .env")
                logger.info("Please add PICOVOICE_ACCESS_KEY to your .env file")
                logger.info("Get your free access key from: https://console.picovoice.ai/")
                return False
            
            if len(access_key) < 10:
                logger.error("PICOVOICE_ACCESS_KEY appears to be invalid (too short)")
                logger.info("Access key should start with something like 'picovoice-...'")
                return False
            
            # Initialize Porcupine with custom "Bible Clock" wake word
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[str(bible_clock_ppn)],
                sensitivities=[0.5]
            )
            
            # Initialize PyAudio with error suppression
            with self._suppress_alsa_messages():
                self.pyaudio = pyaudio.PyAudio()
            
            # Get mic's native sample rate for optimal resampling
            # Find USB microphone device index first
            self.usb_mic_index = self._find_usb_mic_device()
            if self.usb_mic_index is None:
              logger.warning("No microphone found, using default device 0")
              self.usb_mic_index = 0

            # Now get mic's native sample rate
            self.mic_sample_rate = self._get_mic_sample_rate()
            logger.info(f"USB mic native sample rate: {self.mic_sample_rate}Hz")
            
            logger.info(f"Porcupine initialized - Sample rate: {self.porcupine.sample_rate}Hz")
            logger.info(f"Using USB mic device index: {self.usb_mic_index}")
            logger.info("Using custom 'Bible Clock' wake word model")
            
            # Start TTS worker thread
            self._start_tts_worker()
            
            return True
            
        except Exception as e:
            logger.error(f"Porcupine initialization failed: {e}")
            logger.info("Falling back to Google Speech Recognition for wake word")
            self.porcupine = None
            return False
    
    def _initialize_openai_client(self):
        """Initialize OpenAI client with version compatibility."""
        try:
            # Try modern OpenAI API (1.0+)
            from openai import OpenAI
            self.openai_client = OpenAI(
            api_key=self.openai_api_key,
            timeout=60.0  # 60 second timeout for TTS streaming
        )
            self.api_version = "modern"
            logger.info("Using modern OpenAI API (1.0+)")
        except Exception as e:
            logger.warning(f"Modern OpenAI API failed: {e}")
            try:
                # Fallback to legacy API
                import openai
                openai.api_key = self.openai_api_key
                self.openai_client = openai
                self.api_version = "legacy"
                logger.info("Using legacy OpenAI API (0.28)")
            except Exception as e2:
                logger.error(f"Failed to initialize OpenAI: {e2}")
                self.openai_client = None
    
    @contextlib.contextmanager
    def _suppress_alsa_messages(self):
        """Proper context manager to suppress ALSA error messages without file handle leaks."""
        with open(os.devnull, 'w') as fnull:
            with contextlib.redirect_stderr(fnull):
                yield
    
    def _find_usb_mic_device(self):
        """Find USB microphone device index in PyAudio with error suppression."""
        try:
            import pyaudio
            
            # Suppress ALSA errors during device enumeration
            with self._suppress_alsa_messages():
                device_count = self.pyaudio.get_device_count()
                
                for i in range(device_count):
                    try:
                        device_info = self.pyaudio.get_device_info_by_index(i)
                        device_name = device_info.get('name', '').lower()
                        
                        # Look for USB audio devices
                        if any(keyword in device_name for keyword in ['usb', 'fifine', 'pnp', 'microphone']):
                            if device_info.get('maxInputChannels', 0) > 0:
                                logger.info(f"Found USB mic: {device_info['name']} (index {i})")
                                return i
                    except Exception:
                        continue
            
            # If no USB mic found, try to find any input device
            logger.warning("No USB microphone found, looking for any input device...")
            with self._suppress_alsa_messages():
                for i in range(device_count):
                    try:
                        device_info = self.pyaudio.get_device_info_by_index(i)
                        if device_info.get('maxInputChannels', 0) > 0:
                            logger.info(f"No USB mic found. Using fallback input: {device_info['name']} (index {i})")
                            return i
                    except Exception:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding microphone: {e}")
            return None
    
    def _get_mic_sample_rate(self):
        """Detect the native sample rate of the USB microphone."""
        try:
            # Try common sample rates, starting with highest for best quality
            test_rates = [48000, 44100, 32000, 22050, 16000, 8000]
            
            for rate in test_rates:
                try:
                    with self._suppress_alsa_messages():
                        test_stream = self.pyaudio.open(
                            format=self.pyaudio.get_format_from_width(2),
                            channels=1,
                            rate=rate,
                            input=True,
                            input_device_index=self.usb_mic_index,
                            frames_per_buffer=1024
                        )
                        test_stream.close()
                        logger.info(f"Mic supports sample rate: {rate}Hz")
                        return rate
                except Exception:
                    continue
            
            # Default fallback
            logger.warning("Could not detect mic sample rate, using 48000Hz")
            return 48000
            
        except Exception as e:
            logger.error(f"Error detecting mic sample rate: {e}")
            return 48000
    
    def _resample_audio_chunk(self, audio_chunk, source_rate, target_rate):
        """Fast in-memory audio resampling using numpy interpolation."""
        try:
            if source_rate == target_rate:
                return audio_chunk
            
            # Simple linear interpolation for real-time performance
            ratio = target_rate / source_rate
            original_length = len(audio_chunk)
            new_length = int(original_length * ratio)
            
            # Use numpy for fast resampling
            indices = np.linspace(0, original_length - 1, new_length)
            resampled = np.interp(indices, np.arange(original_length), audio_chunk)
            
            return resampled.astype(np.int16)
            
        except Exception as e:
            logger.error(f"Resampling error: {e}")
            return audio_chunk
    
    def listen_for_wake_word(self):
        """Listen for wake word using Porcupine (preferred) or Google Speech Recognition (fallback)."""
        # Don't show "listening" until wake word is detected - just wait silently
        
        if self.porcupine:
            return self._listen_for_wake_word_porcupine()
        else:
            return self._listen_for_wake_word_google()
    
    def _listen_for_wake_word_porcupine(self):
        """Listen for wake word using Porcupine with real-time resampling."""
        try:
            import pyaudio
            
            logger.info("👂 Listening for wake word 'Bible Clock' (Porcupine with resampling)...")
            
            # Calculate frame sizes for resampling
            mic_frame_size = int(self.porcupine.frame_length * self.mic_sample_rate / self.porcupine.sample_rate)
            
            # Create audio stream at mic's native sample rate
            with self._suppress_alsa_messages():
                audio_stream = self.pyaudio.open(
                    rate=self.mic_sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    input_device_index=self.usb_mic_index,
                    frames_per_buffer=mic_frame_size
                )
            
            logger.info(f"Audio stream: {self.mic_sample_rate}Hz → {self.porcupine.sample_rate}Hz")
            
            while True:
                try:
                    # Read audio at mic's native rate
                    pcm_bytes = audio_stream.read(mic_frame_size, exception_on_overflow=False)
                    
                    # Convert to numpy array
                    pcm_array = np.frombuffer(pcm_bytes, dtype=np.int16)
                    
                    # Resample to Porcupine's required rate (16kHz)
                    resampled = self._resample_audio_chunk(
                        pcm_array, self.mic_sample_rate, self.porcupine.sample_rate
                    )
                    
                    # Ensure we have exactly the right frame size
                    if len(resampled) >= self.porcupine.frame_length:
                        frame = resampled[:self.porcupine.frame_length]
                        
                        # Process with Porcupine
                        keyword_index = self.porcupine.process(frame.tolist())
                        
                        if keyword_index >= 0:
                            # Check if voice control is still enabled before processing
                            if not self.enabled or not self.listening:
                                logger.debug("Wake word detected but voice control is disabled - ignoring")
                                continue
                                
                            logger.info("🎯 Wake word 'Bible Clock' detected by Porcupine!")
                            # Record wake word detection time
                            self._reset_metrics()
                            self.metrics['wake_word_time'] = time_module.time()
                            self._update_visual_state("wake_detected", "Wake word detected!")
                            audio_stream.stop_stream()
                            audio_stream.close()
                            return True
                        
                except Exception as e:
                    logger.warning(f"Porcupine processing error: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Porcupine wake word detection error: {e}")
            return False
    
    def _listen_for_wake_word_google(self):
        """Fallback wake word detection using Google Speech Recognition."""
        try:
            logger.info(f"👂 Listening for wake word '{self.wake_word}' (Google SR fallback)...")
            
            while True:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                # Record from USB microphone
                result = subprocess.run([
                    'arecord', '-D', self.usb_mic_device,
                    '-f', 'S16_LE', '-r', '16000', '-c', '1',
                    '-d', '2', temp_path
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Recording failed: {result.stderr}")
                    os.unlink(temp_path)
                    continue
                
                try:
                    with sr.AudioFile(temp_path) as source:
                        audio = self.recognizer.record(source)
                    
                    try:
                        text = self.recognizer.recognize_google(audio).lower()
                        logger.info(f"Heard: '{text}'")
                        
                        # Check for wake word variations
                        wake_variations = ['bible clock', 'bible', 'clock', 'computer']
                        if any(word in text for word in wake_variations):
                            # Check if voice control is still enabled before processing
                            if not self.enabled or not self.listening:
                                logger.debug("Wake word detected but voice control is disabled - ignoring")
                                continue
                                
                            logger.info(f"🎯 Wake word detected in: '{text}'")
                            self._reset_metrics()
                            self.metrics['wake_word_time'] = time_module.time()
                            self._update_visual_state("wake_detected", "Wake word detected!")
                            os.unlink(temp_path)
                            return True
                            
                    except sr.UnknownValueError:
                        pass  # No speech detected
                    except sr.RequestError as e:
                        logger.warning(f"Speech recognition error: {e}")
                        
                except Exception as e:
                    logger.error(f"Wake word check error: {e}")
                
                os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
            return False
    
    def _detect_silence(self, audio_chunk, silence_threshold=500):
        """Simple VAD using RMS energy detection."""
        rms = np.sqrt(np.mean(audio_chunk.astype(np.float64) ** 2))
        return rms < silence_threshold
    
    def listen_for_command(self):
        """Listen for voice command with VAD-based automatic end detection."""
        try:
            import pyaudio
            import wave
            
            self._update_visual_state("recording", "Recording command...")
            print("🎤 Listening... speak your command now!")
            
            # Record command start time
            self.metrics['command_start_time'] = time_module.time()
            
            # Audio recording parameters - use mic's native rate
            mic_sample_rate = self.mic_sample_rate  # Use detected mic rate (48kHz)
            target_sample_rate = 16000  # For speech recognition
            chunk_size = 1024
            silence_threshold = 500
            min_silence_duration = 1.2  # Increased to allow natural speech pauses
            max_recording_duration = 15  # Increased to allow longer questions
            
            audio_chunks = []
            silence_chunks = 0
            silence_chunks_needed = int(min_silence_duration * mic_sample_rate / chunk_size)
            total_chunks = 0
            max_chunks = int(max_recording_duration * mic_sample_rate / chunk_size)
            
            # Create audio stream at mic's native sample rate
            with self._suppress_alsa_messages():
                stream = self.pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=mic_sample_rate,  # Use mic's native rate
                    input=True,
                    input_device_index=self.usb_mic_index,
                    frames_per_buffer=chunk_size
                )
            
            logger.info("Recording with VAD - speak now...")
            recording_started = False
            
            # Add timeout timer to prevent stuck recording state
            def timeout_handler():
                if stream:
                    try:
                        stream.stop_stream()
                        stream.close()
                    except:
                        pass
                self._update_visual_state("timeout", "Recording timeout")
                threading.Timer(2.0, lambda: self._update_visual_state("ready", "Ready")).start()
            
            timeout_timer = threading.Timer(max_recording_duration + 2, timeout_handler)
            timeout_timer.start()
            
            try:
                while total_chunks < max_chunks:
                    # Read audio chunk
                    audio_data = stream.read(chunk_size, exception_on_overflow=False)
                    audio_chunk = np.frombuffer(audio_data, dtype=np.int16)
                    
                    # Detect if this chunk contains speech
                    is_silent = self._detect_silence(audio_chunk, silence_threshold)
                    
                    if not is_silent:
                        # Speech detected
                        recording_started = True
                        silence_chunks = 0
                        audio_chunks.append(audio_data)
                    elif recording_started:
                        # Silence after speech started
                        silence_chunks += 1
                        audio_chunks.append(audio_data)
                        
                        # Check if we've had enough silence to end recording
                        if silence_chunks >= silence_chunks_needed:
                            logger.info("Silence detected, ending recording")
                            break
                    
                    total_chunks += 1
            
            finally:
                # Cancel timeout timer and clean up stream
                timeout_timer.cancel()
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
            
            if not audio_chunks:
                self._update_visual_state("error", "No speech detected")
                print("❓ No speech detected")
                return None
            
            # Combine all audio chunks
            combined_audio = b''.join(audio_chunks)
            
            # Convert audio to numpy array for resampling
            audio_array = np.frombuffer(combined_audio, dtype=np.int16)
            
            # Resample from mic rate to target rate for speech recognition
            if mic_sample_rate != target_sample_rate:
                resampled_audio = self._resample_audio_chunk(
                    audio_array, mic_sample_rate, target_sample_rate
                )
                resampled_bytes = resampled_audio.astype(np.int16).tobytes()
            else:
                resampled_bytes = combined_audio
            
            # Convert to speech recognition format
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Write WAV file at 16kHz for speech recognition
                with wave.open(temp_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(target_sample_rate)  # 16kHz for speech recognition
                    wav_file.writeframes(resampled_bytes)
            
            self._update_visual_state("processing", "Processing command...")
            
            # Use speech recognition on the recorded file
            with sr.AudioFile(temp_path) as source:
                audio = self.recognizer.record(source)
            
            command = self.recognizer.recognize_google(audio).lower()
            print(f"✅ Command: '{command}'")
            
            # Record command end time
            self.metrics['command_end_time'] = time_module.time()
            
            # Clean up
            os.unlink(temp_path)
            self._cleanup_audio_buffers()  # Memory cleanup
            return command
            
        except sr.UnknownValueError:
            error_msg = "Couldn't understand speech - try speaking more clearly"
            self._update_visual_state("error", "Couldn't understand")
            logger.warning(f"❓ {error_msg}")
            print(f"❓ {error_msg}")
            # Clear recording state after a delay
            threading.Timer(3.0, lambda: self._update_visual_state("ready", "Ready")).start()
            return None
        except sr.RequestError as e:
            error_msg = f"Speech recognition service error: {str(e)}"
            self._update_visual_state("error", "Recognition service error")
            logger.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            # Clear recording state after a delay
            threading.Timer(3.0, lambda: self._update_visual_state("ready", "Ready")).start()
            return None
        except Exception as e:
            error_msg = f"Speech processing error: {str(e)}"
            self._update_visual_state("error", "Processing error")
            logger.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            # Clear recording state after a delay
            threading.Timer(3.0, lambda: self._update_visual_state("ready", "Ready")).start()
            return None
    
    def get_current_metrics(self):
        """Get current performance metrics."""
        return self.metrics.copy()
    
    @property
    def enabled(self):
        """Get enabled state."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value):
        """Set enabled state and sync listening state."""
        was_enabled = getattr(self, '_enabled', False)
        self._enabled = value
        if hasattr(self, 'listening'):
            self.listening = value
            # Only show visual messages when actually toggling (not during initialization)
            if was_enabled != value and hasattr(self, '_initialized'):
                if value:  # Being enabled
                    self._update_visual_state("listening", "Voice control ready - Say 'Bible Clock' to begin")
                else:  # Being disabled
                    self._update_visual_state("idle", "Wake word detection stopped")
                    # Clear the message after 3 seconds and restore normal display
                    threading.Timer(3.0, lambda: self._restore_normal_display()).start()

    def get_voice_status(self):
        """Get comprehensive voice control status for web interface compatibility."""
        return {
            'enabled': self.enabled,
            'listening': hasattr(self, 'listening') and getattr(self, 'listening', False),
            'wake_word': self.wake_word,
            'chatgpt_enabled': self.enabled and bool(self.openai_api_key),
            'help_enabled': True,  # Basic help is always available
            'respeaker_enabled': False,  # VoiceAssistant doesn't use ReSpeaker
            'voice_rate': 150,  # Default rate for compatibility
            'voice_volume': 0.8,  # Default volume for compatibility
            'voice_selection': getattr(self, 'voice_selection', self.tts_voice),
            'tts_voice': self.tts_voice,
            'tts_engine': self.tts_engine,
            'tts_model': self.tts_model,
            'conversation_length': len(self.conversation_manager.conversation_history) if hasattr(self.conversation_manager, 'conversation_history') else 0,
            'available_commands': ['chat', 'help', 'status'],  # Basic commands
            'chatgpt_api_key': bool(self.openai_api_key),
            # Audio input/output controls
            'audio_input_enabled': True,
            'audio_output_enabled': True,
            'force_respeaker_output': False,
            # ReSpeaker settings (not used but needed for compatibility)
            'respeaker_channels': 6,
            'respeaker_sample_rate': 16000,
            'respeaker_chunk_size': 1024,
            # Additional voice settings
            'voice_timeout': self.voice_timeout,
            'phrase_limit': 15,  # Default for compatibility
            'help_section_pause': 2  # Default for compatibility
        }
    
    def run_main_loop(self):
        """Main voice interaction loop with controllable listening state."""
        try:
            # Show listening state when starting up
            if self.enabled and self.listening:
                self._update_visual_state("listening", "Voice control ready - Say 'Bible Clock' to begin")
            
            while not self.should_stop:
                if self.enabled and self.listening:
                    # Wait for wake word when listening is enabled
                    if self.listen_for_wake_word():
                        # Wake word detected, listen for command
                        command = self.listen_for_command()
                        if command:
                            self.process_voice_command(command)
                else:
                    # When not listening, wait briefly to prevent busy loop
                    time_module.sleep(0.1)
        except KeyboardInterrupt:
            self._update_visual_state("shutdown", "Voice assistant stopped")
            logger.info("Voice assistant stopped by user")
        except Exception as e:
            self._update_visual_state("error", f"Main loop error: {str(e)}")
            logger.error(f"Main loop error: {e}")
    
    def start_listening(self):
        """Start wake word detection."""
        self.listening = True
        self._update_visual_state("listening", "Voice control ready - Say 'Bible Clock' to begin")
        logger.info("Voice assistant listening started")
    
    def stop_listening(self):
        """Stop wake word detection."""
        self.listening = False
        self._update_visual_state("idle", "Wake word detection stopped")
        logger.info("Voice assistant listening stopped")
        
        # Clear the message after 3 seconds and restore normal display
        threading.Timer(3.0, lambda: self._restore_normal_display()).start()
    
    def _restore_normal_display(self):
        """Restore normal Bible verse display after voice control messages."""
        try:
            logger.info("🔄 Restoring normal display after voice control stop")
            if self.visual_feedback:
                self.visual_feedback("restore", None)
            else:
                logger.warning("No visual feedback callback available for restoration")
        except Exception as e:
            logger.error(f"Display restoration failed: {e}")
    
    def shutdown(self):
        """Shutdown the voice assistant completely."""
        self.should_stop = True
        self.listening = False
        self._update_visual_state("shutdown", "Voice assistant shutting down")
        logger.info("Voice assistant shutdown initiated")
    
    def _start_interrupt_detection(self):
        """Start background thread to detect wake word interrupts during TTS."""
        if self.porcupine and not self.interrupt_detection_active:
            self.interrupt_detection_active = True
            self.interrupt_thread = threading.Thread(target=self._interrupt_detector, daemon=True)
            self.interrupt_thread.start()
            logger.info("Interrupt detection started")
    
    def _stop_interrupt_detection(self):
        """Stop interrupt detection."""
        self.interrupt_detection_active = False
    
    def _interrupt_detector(self):
        """Background thread that listens for wake word to interrupt current TTS."""
        try:
            import pyaudio
            
            # Calculate frame sizes for resampling
            mic_frame_size = int(self.porcupine.frame_length * self.mic_sample_rate / self.porcupine.sample_rate)
            
            # Create audio stream at mic's native sample rate
            with self._suppress_alsa_messages():
                audio_stream = self.pyaudio.open(
                    rate=self.mic_sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    input_device_index=self.usb_mic_index,
                    frames_per_buffer=mic_frame_size
                )
            
            while self.interrupt_detection_active:
                try:
                    # Read audio at mic's native rate
                    pcm_bytes = audio_stream.read(mic_frame_size, exception_on_overflow=False)
                    pcm_array = np.frombuffer(pcm_bytes, dtype=np.int16)
                    
                    # Resample to Porcupine's required rate
                    resampled = self._resample_audio_chunk(
                        pcm_array, self.mic_sample_rate, self.porcupine.sample_rate
                    )
                    
                    if len(resampled) >= self.porcupine.frame_length:
                        frame = resampled[:self.porcupine.frame_length]
                        keyword_index = self.porcupine.process(frame.tolist())
                        
                        if keyword_index >= 0:
                            logger.info("🔥 Interrupt detected! Canceling current response...")
                            self._update_visual_state("interrupted", "Interrupted - new command")
                            # Signal TTS to stop and clear queue
                            self.tts_interrupt_event.set()
                            # Clear the TTS queue
                            while not self.tts_queue.empty():
                                try:
                                    self.tts_queue.get_nowait()
                                except queue.Empty:
                                    break
                            # Reset metrics for new interaction
                            self._reset_metrics()
                            self.metrics['wake_word_time'] = time_module.time()
                            # Stop interrupt detection temporarily
                            self._stop_interrupt_detection()
                            # Handle new command
                            command = self.listen_for_command()
                            if command:
                                self.process_voice_command(command)
                            return
                        
                except Exception as e:
                    logger.warning(f"Interrupt detection error: {e}")
                    continue
            
            audio_stream.stop_stream()
            audio_stream.close()
            
        except Exception as e:
            logger.error(f"Interrupt detection failed: {e}")
    
    def _start_tts_worker(self):
        """Start the TTS worker thread to prevent overlapping speech."""
        self.tts_thread_running = True
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        logger.info("TTS worker thread started")
    
    def _reset_metrics(self):
        """Reset performance metrics for new interaction."""
        for key in self.metrics:
            self.metrics[key] = None
    
    def _log_metrics(self):
        """Log performance metrics."""
        try:
            if self.metrics['wake_word_time'] and self.metrics['first_speech_time']:
                total_time = self.metrics['first_speech_time'] - self.metrics['wake_word_time']
                
                timings = {
                    'wake_to_command': None,
                    'command_duration': None,
                    'gpt_response_time': None,
                    'gpt_to_speech': None,
                    'total_interaction': total_time
                }
                
                if self.metrics['command_start_time']:
                    timings['wake_to_command'] = self.metrics['command_start_time'] - self.metrics['wake_word_time']
                
                if self.metrics['command_end_time'] and self.metrics['command_start_time']:
                    timings['command_duration'] = self.metrics['command_end_time'] - self.metrics['command_start_time']
                
                if self.metrics['gpt_first_response_time'] and self.metrics['gpt_start_time']:
                    timings['gpt_response_time'] = self.metrics['gpt_first_response_time'] - self.metrics['gpt_start_time']
                
                if self.metrics['first_speech_time'] and self.metrics['gpt_first_response_time']:
                    timings['gpt_to_speech'] = self.metrics['first_speech_time'] - self.metrics['gpt_first_response_time']
                
                logger.info("📊 Performance Metrics:")
                logger.info(f"  Total interaction: {total_time:.2f}s")
                if timings['wake_to_command']:
                    logger.info(f"  Wake → Command: {timings['wake_to_command']:.2f}s")
                if timings['command_duration']:
                    logger.info(f"  Command duration: {timings['command_duration']:.2f}s")
                if timings['gpt_response_time']:
                    logger.info(f"  GPT response: {timings['gpt_response_time']:.2f}s")
                if timings['gpt_to_speech']:
                    logger.info(f"  GPT → Speech: {timings['gpt_to_speech']:.2f}s")
                
                return timings
                
        except Exception as e:
            logger.error(f"Metrics logging error: {e}")
        return None
    
    def _tts_worker(self):
        """Worker thread that processes TTS queue to prevent overlapping speech."""
        while self.tts_thread_running:
            try:
                # Get next TTS task from queue (blocks until available)
                tts_text = self.tts_queue.get(timeout=1.0)
                if tts_text is None:  # Shutdown signal
                    break
                
                # Check for interrupt before speaking
                if self.tts_interrupt_event.is_set():
                    self.tts_interrupt_event.clear()
                    logger.info("TTS interrupted, skipping queued message")
                    self.tts_queue.task_done()
                    continue
                
                # Record first speech time for metrics
                if self.metrics['first_speech_time'] is None:
                    self.metrics['first_speech_time'] = time_module.time()
                
                # Update visual state
                self._update_visual_state("speaking", f"Speaking: {tts_text[:30]}...")
                
                # Temporarily disable interrupt detection to avoid mic conflicts
                # TODO: Implement proper audio device sharing in future version
                # self._start_interrupt_detection()
                
                # Speak the text (this will block until complete)
                self._speak_with_amy_direct(tts_text)
                
                # self._stop_interrupt_detection()
                
                # Mark task as done
                self.tts_queue.task_done()
                
                # Log metrics if this was the first speech
                if self.metrics['first_speech_time'] and not hasattr(self, '_metrics_logged'):
                    self._log_metrics()
                    self._metrics_logged = True
                
                # Update visual state back to ready
                self._update_visual_state("ready", "Voice assistant ready")
                
            except queue.Empty:
                continue  # Timeout, check if still running
            except Exception as e:
                logger.error(f"TTS worker error: {e}")
    
    def _cleanup_audio_buffers(self):
        """Clean up audio buffers and force garbage collection."""
        try:
            import gc
            # Clean up any lingering audio chunks
            if hasattr(self, 'audio_chunks'):
                del self.audio_chunks
            
            # Force garbage collection to free memory
            gc.collect()
            logger.debug("Audio buffer cleanup completed")
        except Exception as e:
            logger.warning(f"Audio buffer cleanup error: {e}")
    
    def queue_tts(self, text, priority=False):
        """Queue text for TTS with memory-safe size limits."""
        try:
            if priority:
                # Clear queue and add this as priority
                while not self.tts_queue.empty():
                    try:
                        self.tts_queue.get_nowait()
                    except queue.Empty:
                        break
            else:
                # Check queue size limit for non-priority items
                if self.tts_queue.qsize() >= self.MAX_TTS_QUEUE_SIZE:
                    logger.warning(f"TTS queue full ({self.tts_queue.qsize()}/{self.MAX_TTS_QUEUE_SIZE}), dropping oldest item")
                    try:
                        dropped_text = self.tts_queue.get_nowait()
                        logger.debug(f"Dropped TTS: {dropped_text[:30]}...")
                    except queue.Empty:
                        pass
            
            self.tts_queue.put(text)
            logger.debug(f"Queued TTS ({self.tts_queue.qsize()}/{self.MAX_TTS_QUEUE_SIZE}): {text[:50]}...")
            
        except Exception as e:
            logger.error(f"Error queuing TTS: {e}")
    
    def _speak_with_amy_direct(self, text):
        """Direct TTS without queueing (used by worker thread)."""
        try:
            logger.info(f"Speaking: {text[:50]}...")
            
            # Set lower process priority to prevent system lockup on Pi 3B+
            current_priority = os.nice(0)
            os.nice(5)
            
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate audio with Piper - balanced speed and CPU optimization
            result = subprocess.run([
                'taskset', '-c', '0,1',  # Limit to first 2 CPU cores
                'piper',
                '--model', self.piper_model_path,
                '--output_file', temp_path,
                '--length_scale', '0.85',  # Speak 15% faster (more natural)
                '--noise_scale', '0.667',  # Default noise for quality
                '--sentence_silence', '0.2'  # Slightly reduced pauses
            ], input=text, text=True, capture_output=True)
            
            if result.returncode == 0:
                # Play audio through correct USB speakers with maximum speed
                subprocess.run(['aplay', '-D', self.usb_speaker_device, 
                              '--buffer-size=512', '--period-size=256', temp_path])
                logger.info("Audio played successfully")
            else:
                logger.error(f"Piper TTS failed: {result.stderr}")
            
            # Clean up
            os.unlink(temp_path)
            
            # ✅ RESTORE display after Piper TTS completion
            self._restore_display_after_tts()
            
        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
            # Restore display even if TTS failed
            self._restore_display_after_tts()
    
    def speak_with_amy(self, text, priority=False):
        """Queue text for TTS to prevent overlapping speech."""
        self.queue_tts(text, priority=priority)
    
    def _play_openai_tts_stream(self, text):
        """Generate speech using OpenAI TTS API with fast streaming playback and mic management."""
        try:
            logger.info("🔊 Requesting OpenAI TTS...")
            
            # Record first speech time for metrics
            if self.metrics['first_speech_time'] is None:
                self.metrics['first_speech_time'] = time_module.time()
            
            # Update visual state
            self._update_visual_state("speaking", f"Speaking via OpenAI TTS...")
            
            # Generate speech using OpenAI TTS API with configurable settings
            logger.info(f"🔊 TTS Config - Model: {self.tts_model}, Voice: {self.tts_voice}, Format: {self.tts_audio_format}")
            response = self.openai_client.audio.speech.create(
                model=self.tts_model,
                voice=self.tts_voice,
                input=text,
                response_format=self.tts_audio_format
            )
            
            # ✅ PAUSE mic before playback to avoid audio conflict
            try:
                if hasattr(self, 'pyaudio') and self.pyaudio:
                    self.pyaudio.terminate()
                    logger.info("🎙️ Paused audio input before playback")
            except Exception as pause_err:
                logger.warning(f"Failed to pause mic: {pause_err}")
            
            logger.info("🔊 Streaming OpenAI speech immediately...")
            
            # Use ffplay for MP3 playback (handles format automatically)
            try:
                logger.info("🔊 Playing audio with ffplay...")
                
                with tempfile.NamedTemporaryFile(suffix=f".{self.tts_audio_format}", delete=False) as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name
                
                # Use ffplay which handles MP3/WAV automatically and routes to USB speakers
                result = subprocess.run([
                    "ffplay", "-nodisp", "-autoexit", "-volume", "70",
                    tmp_path
                ], capture_output=True, timeout=30)
                
                os.unlink(tmp_path)
                
                if result.returncode == 0:
                    logger.info("✅ Audio playback successful")
                else:
                    logger.warning(f"ffplay returned error code {result.returncode}")
                
            except Exception as play_error:
                logger.warning(f"Audio playback failed: {play_error}")
                
                # Fallback: try direct aplay with WAV format only
                if self.tts_audio_format == "wav":
                    try:
                        aplay_process = subprocess.Popen([
                            "aplay", "-D", self.usb_speaker_device,
                            "-f", "S16_LE", "-r", "24000", "-c", "1", "-"
                        ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
                        
                        aplay_process.communicate(input=response.content)
                        logger.info("✅ Fallback aplay playback complete")
                    except Exception as aplay_error:
                        logger.error(f"All playback methods failed: {aplay_error}")
            
            # 🔁 RESTART mic after playback
            try:
                import pyaudio
                with self._suppress_alsa_messages():
                    self.pyaudio = pyaudio.PyAudio()
                self.usb_mic_index = self._find_usb_mic_device()
                logger.info("🎙️ Resumed audio input after playback")
            except Exception as resume_err:
                logger.warning(f"Failed to restart mic: {resume_err}")
            
            # ✅ RESTORE display after TTS completion
            self._restore_display_after_tts()
                
        except Exception as e:
            logger.error(f"OpenAI TTS playback failed: {e}")
            
            if self.allow_piper_fallback:
                logger.info("Falling back to Piper TTS...")
                self.queue_tts(text)
            else:
                logger.warning("❌ Skipping TTS: OpenAI failed and Piper fallback is disabled (ALLOW_PIPER_FALLBACK=false)")
                # Restore display even if TTS failed
                self._restore_display_after_tts()

    
    def query_chatgpt(self, question):
        """Send question to ChatGPT using streaming API with conversation context and metrics."""
        chatgpt_start_time = time_module.time()
        
        try:
            if not self.openai_client:
                return "I need an OpenAI API key to answer questions. Please configure it in your environment."
            
            self._update_visual_state("thinking", "Asking ChatGPT...")
            
            # Check if this is a verse explanation request (disable early TTS for complete responses)
            is_verse_explanation = any(phrase in question.lower() for phrase in [
                'explain', 'meaning', 'means', 'interpret', 'what does', 'tell me about',
                'verse', 'passage', 'scripture', 'biblical', 'theology', 'theological'
            ])
            logger.info(f"Query type - Verse explanation: {is_verse_explanation}")
            
            # Get current verse context
            current_verse = ""
            if self.verse_manager:
                verse_data = self.verse_manager.get_current_verse()
                if verse_data:
                    current_verse = f"Current verse displayed: {verse_data.get('reference', '')} - {verse_data.get('text', '')}"
            
            # Get conversation context for multi-turn conversations
            conversation_context = self.conversation_manager.get_conversation_context(turns_back=3)
            
            # Create enhanced system prompt with context
            context_section = ""
            if conversation_context:
                context_section = f"\n\nRecent conversation context:\n{conversation_context}\n"
            
            full_system_prompt = f"""{self.system_prompt}
            
{current_verse}{context_section}

When asked to "explain this verse" or similar, refer to the current verse displayed above.
For follow-up questions like "continue", "tell me more", or "explain further", refer to our previous conversation."""
            
            # Record GPT start time for metrics
            self.metrics['gpt_start_time'] = time_module.time()
            
            # Use streaming for real-time response
            if self.api_version == "modern":
                response_stream = self.openai_client.chat.completions.create(
                    model=self.chatgpt_model,
                    messages=[
                        {"role": "system", "content": full_system_prompt},
                        {"role": "user", "content": question}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=0.7,
                    stream=True  # Enable streaming for real-time response
                )
                
                # Collect response with improved TTS optimization
                full_response = ""
                word_count = 0
                early_tts_sent = False
                stream_start_time = time_module.time()
                last_content_time = time_module.time()
                stream_timeout = 30  # 30 second timeout for streaming
                pause_threshold = 3.0  # 3 seconds of no new content = likely complete
                
                # Dynamic word thresholds based on query type
                if is_verse_explanation:
                    min_word_threshold = 50  # Higher threshold for verse explanations
                    pause_threshold = 4.0   # Longer pause for theological explanations
                    logger.info("📖 Using extended thresholds for verse explanation")
                else:
                    min_word_threshold = 25  # Moderate threshold for other questions
                    pause_threshold = 3.0   # Standard pause for quick answers
                
                for chunk in response_stream:
                    current_time = time_module.time()
                    
                    # Check for timeout
                    if current_time - stream_start_time > stream_timeout:
                        logger.warning(f"⏰ ChatGPT streaming timeout after {stream_timeout}s")
                        if full_response.strip():
                            logger.info("🔄 Using partial response due to timeout")
                            break
                        else:
                            logger.error("❌ No response received before timeout")
                            return "Sorry, I'm having trouble processing your request. Please try again."
                    
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        word_count += len(content.split())
                        last_content_time = current_time
                        
                        # Record first response time
                        if self.metrics['gpt_first_response_time'] is None:
                            self.metrics['gpt_first_response_time'] = current_time
                    
                    # Check for early TTS trigger with improved logic
                    if (not early_tts_sent and word_count >= min_word_threshold and 
                        len(full_response.strip()) > 50):
                        
                        # Calculate time since last content (speech pause detection)
                        time_since_content = current_time - last_content_time
                        
                        # Check if response ends with strong punctuation (complete thought)
                        trimmed_response = full_response.strip()
                        ends_with_punctuation = any(trimmed_response.endswith(punct) for punct in ['.', '!', '?'])
                        
                        # For verse explanations: ONLY trigger if we have both conditions
                        # For other queries: trigger on word count OR pause detection
                        should_trigger = False
                        
                        if is_verse_explanation:
                            # Strict mode: need BOTH sufficient words AND natural pause AND punctuation
                            should_trigger = (word_count >= min_word_threshold and 
                                            time_since_content >= pause_threshold and 
                                            ends_with_punctuation)
                            if should_trigger:
                                logger.info(f"📖 Verse explanation complete - Words: {word_count}, Pause: {time_since_content:.1f}s")
                        else:
                            # Flexible mode: word count OR pause detection with punctuation
                            should_trigger = ((word_count >= min_word_threshold and ends_with_punctuation) or
                                            (time_since_content >= pause_threshold and ends_with_punctuation))
                            if should_trigger:
                                logger.info(f"💬 Quick response ready - Words: {word_count}, Pause: {time_since_content:.1f}s")
                        
                        # Disable early TTS to prevent incomplete responses
                        # if should_trigger:
                        #     logger.info("🚀 Smart TTS trigger - starting speech for partial response")
                        #     self._play_openai_tts_stream(trimmed_response)
                        #     early_tts_sent = True
                        #     return trimmed_response
                
                # Always use OpenAI TTS for the complete response (early TTS disabled)
                if full_response.strip():
                    tts_start_time = time_module.time()
                    self._play_openai_tts_stream(full_response.strip())
                    self.timing_metrics['tts_generation_time'] = time_module.time() - tts_start_time
                
                # Record conversation with metrics
                self.timing_metrics['chatgpt_processing_time'] = time_module.time() - chatgpt_start_time
                self.conversation_manager.record_conversation(question, full_response.strip(), self.timing_metrics)
                
                logger.info(f"ChatGPT streaming response: {full_response[:100]}...")
                return full_response
                
            else:
                # Legacy API fallback (non-streaming)
                response = self.openai_client.ChatCompletion.create(
                    model=self.chatgpt_model,
                    messages=[
                        {"role": "system", "content": full_system_prompt},
                        {"role": "user", "content": question}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=0.7
                )
                answer = response.choices[0].message.content.strip()
                
                # Record first response time for legacy API
                if self.metrics['gpt_first_response_time'] is None:
                    self.metrics['gpt_first_response_time'] = time_module.time()
                
                # Use OpenAI TTS for legacy API response too
                if answer.strip():
                    tts_start_time = time_module.time()
                    self._play_openai_tts_stream(answer.strip())
                    self.timing_metrics['tts_generation_time'] = time_module.time() - tts_start_time
                
                # Record conversation with metrics for legacy API
                self.timing_metrics['chatgpt_processing_time'] = time_module.time() - chatgpt_start_time
                self.conversation_manager.record_conversation(question, answer.strip(), self.timing_metrics)
                
                logger.info(f"ChatGPT response: {answer[:100]}...")
                return answer
            
        except Exception as e:
            logger.error(f"ChatGPT query failed: {e}")
            error_msg = f"I'm sorry, I encountered an error processing your question: {str(e)}"
            self._update_visual_state("error", error_msg)
            return error_msg
    
    def process_voice_command(self, command_text):
        """Process the voice command."""
        try:
            self._update_visual_state("processing", f"Processing: {command_text}")
            
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
                    
            elif any(phrase in command_text for phrase in ['explain this verse', 'explain verse', 'what does this mean', 'explain this']):
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
                # Send to ChatGPT for Bible questions (streaming will handle TTS automatically)
                response = self.query_chatgpt(command_text)
                # Note: streaming ChatGPT already handles TTS, no need to speak again
                return  # Exit early for ChatGPT responses
            
            # For built-in commands, speak the response
            if response:
                self.speak_with_amy(response, priority=True)
                
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            error_msg = "I'm sorry, I encountered an error processing your request."
            self._update_visual_state("error", error_msg)
            self.speak_with_amy(error_msg, priority=True)
    
    def mark_initialized(self):
        """Mark the voice assistant as fully initialized to enable visual feedback."""
        self._initialized = True
        logger.info("Voice assistant marked as initialized - visual feedback enabled")
