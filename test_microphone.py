#!/usr/bin/env python3
"""
Test script for ReSpeaker HAT microphone functionality.
Tests audio recording, playback, and voice recognition capabilities.
"""

import os
import sys
import time
import wave
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_audio_devices():
    """Test and list available audio devices."""
    print("🎤 Testing Audio Devices")
    print("=" * 40)
    
    try:
        import pyaudio
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        print("📋 Available Audio Devices:")
        print()
        
        # List all audio devices
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            device_type = []
            
            if info['maxInputChannels'] > 0:
                device_type.append("INPUT")
            if info['maxOutputChannels'] > 0:
                device_type.append("OUTPUT")
                
            if not device_type:
                device_type = ["NONE"]
            
            print(f"Device {i}: {info['name']}")
            print(f"  Type: {'/'.join(device_type)}")
            print(f"  Channels: In={info['maxInputChannels']}, Out={info['maxOutputChannels']}")
            print(f"  Sample Rate: {info['defaultSampleRate']}")
            print()
        
        # Find ReSpeaker devices
        respeaker_devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if 'seeed' in info['name'].lower() or 'respeaker' in info['name'].lower():
                respeaker_devices.append((i, info))
        
        if respeaker_devices:
            print("✅ ReSpeaker HAT devices found:")
            for device_id, info in respeaker_devices:
                print(f"  Device {device_id}: {info['name']}")
        else:
            print("⚠️  No ReSpeaker HAT devices found")
            print("   Make sure the HAT is properly installed and drivers are loaded")
        
        p.terminate()
        return respeaker_devices
        
    except ImportError:
        print("❌ PyAudio not installed. Run: pip install pyaudio")
        return []
    except Exception as e:
        print(f"❌ Error testing audio devices: {e}")
        return []

def test_alsa_devices():
    """Test ALSA audio devices."""
    print("\n🔊 Testing ALSA Devices")
    print("=" * 40)
    
    try:
        import subprocess
        
        # List ALSA playback devices
        print("📤 ALSA Playback Devices:")
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("❌ No playback devices found")
        
        print("\n📥 ALSA Recording Devices:")
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("❌ No recording devices found")
            
        # Check for ReSpeaker in ALSA
        result = subprocess.run(['cat', '/proc/asound/cards'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n🎵 Sound Cards:")
            print(result.stdout)
            
            if 'seeed' in result.stdout.lower():
                print("✅ ReSpeaker HAT detected in ALSA")
            else:
                print("⚠️  ReSpeaker HAT not found in ALSA")
        
    except Exception as e:
        print(f"❌ Error testing ALSA devices: {e}")

def record_test_audio(duration=5, device_id=None):
    """Record test audio from microphone."""
    print(f"\n🎙️  Recording {duration} seconds of audio...")
    print("=" * 40)
    
    try:
        import pyaudio
        
        # Audio parameters
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        
        p = pyaudio.PyAudio()
        
        # Use specific device or default
        stream_kwargs = {
            'format': FORMAT,
            'channels': CHANNELS,
            'rate': RATE,
            'input': True,
            'frames_per_buffer': CHUNK
        }
        
        if device_id is not None:
            stream_kwargs['input_device_index'] = device_id
            device_info = p.get_device_info_by_index(device_id)
            print(f"📱 Using device: {device_info['name']}")
        else:
            print("📱 Using default input device")
        
        stream = p.open(**stream_kwargs)
        
        print("🔴 Recording... Speak into the microphone!")
        
        frames = []
        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            
            # Simple volume indicator
            import struct
            if i % 10 == 0:  # Update every ~0.1 seconds
                volume = max(struct.unpack('h' * (len(data) // 2), data))
                bars = min(20, volume // 1000)
                print(f"\r📊 Volume: {'█' * bars}{' ' * (20 - bars)} {volume}", end='')
        
        print("\n⏹️  Recording stopped")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Save recording
        filename = 'test_recording.wav'
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print(f"💾 Audio saved as: {filename}")
        return filename
        
    except ImportError:
        print("❌ PyAudio not installed")
        return None
    except Exception as e:
        print(f"❌ Recording failed: {e}")
        return None

def play_test_audio(filename):
    """Play back recorded audio."""
    if not filename or not os.path.exists(filename):
        print("❌ No audio file to play")
        return
    
    print(f"\n🔊 Playing back recorded audio: {filename}")
    print("=" * 40)
    
    try:
        import subprocess
        
        # Try different audio players
        players = ['aplay', 'paplay', 'cvlc', 'mplayer']
        
        for player in players:
            try:
                result = subprocess.run([player, filename], 
                                     timeout=10, 
                                     capture_output=True)
                if result.returncode == 0:
                    print(f"✅ Playback successful using {player}")
                    return
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        print("❌ Could not play audio file")
        print("   Try manually: aplay test_recording.wav")
        
    except Exception as e:
        print(f"❌ Playback failed: {e}")

def test_speech_recognition():
    """Test speech recognition functionality."""
    print("\n🗣️  Testing Speech Recognition")
    print("=" * 40)
    
    try:
        import speech_recognition as sr
        
        # Initialize recognizer
        r = sr.Recognizer()
        
        # Test microphone access
        with sr.Microphone() as source:
            print("🎙️  Adjusting for ambient noise... (stay quiet)")
            r.adjust_for_ambient_noise(source, duration=2)
            print("✅ Noise adjustment complete")
            
            print("\n🎤 Say something! (5 second timeout)")
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=3)
                print("🎵 Audio captured, processing...")
                
                # Try to recognize speech
                try:
                    text = r.recognize_google(audio)
                    print(f"✅ Recognized: '{text}'")
                except sr.UnknownValueError:
                    print("⚠️  Could not understand audio")
                except sr.RequestError as e:
                    print(f"❌ Google Speech Recognition error: {e}")
                    
            except sr.WaitTimeoutError:
                print("⏰ No speech detected (timeout)")
                
    except ImportError:
        print("❌ SpeechRecognition not installed")
        print("   Run: pip install SpeechRecognition")
    except Exception as e:
        print(f"❌ Speech recognition test failed: {e}")

def test_bible_clock_voice():
    """Test Bible Clock voice control integration."""
    print("\n📖 Testing Bible Clock Voice Control")
    print("=" * 40)
    
    try:
        # Load environment
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        
        # Try to import voice control
        from voice_control import BibleClockVoiceControl
        
        print("🎤 Creating voice control instance...")
        voice_control = BibleClockVoiceControl(None, None, None)
        
        if voice_control.enabled:
            print("✅ Voice control enabled")
            print(f"🎯 Wake word: '{voice_control.wake_word}'")
            print(f"🔊 Voice rate: {voice_control.voice_rate}")
            print(f"📢 Voice volume: {voice_control.voice_volume}")
            
            if hasattr(voice_control, 'respeaker_enabled'):
                print(f"🎧 ReSpeaker enabled: {voice_control.respeaker_enabled}")
            
            # Test TTS
            print("\n🗣️  Testing text-to-speech...")
            if voice_control.tts_engine:
                voice_control.tts_engine.say("Bible Clock microphone test successful")
                voice_control.tts_engine.runAndWait()
                print("✅ Text-to-speech working")
            else:
                print("❌ Text-to-speech not available")
        else:
            print("⚠️  Voice control disabled in configuration")
            
    except ImportError as e:
        print(f"❌ Could not import Bible Clock voice control: {e}")
    except Exception as e:
        print(f"❌ Bible Clock voice test failed: {e}")

def main():
    """Run comprehensive microphone tests."""
    print("🎤 Bible Clock - ReSpeaker HAT Microphone Test")
    print("=" * 50)
    print()
    
    # Test 1: Audio devices
    respeaker_devices = test_audio_devices()
    
    # Test 2: ALSA devices
    test_alsa_devices()
    
    # Test 3: Record audio
    print("\n" + "=" * 50)
    input("Press Enter to start 5-second audio recording test...")
    
    # Use ReSpeaker device if found, otherwise default
    device_id = None
    if respeaker_devices:
        device_id = respeaker_devices[0][0]  # Use first ReSpeaker device
    
    filename = record_test_audio(duration=5, device_id=device_id)
    
    # Test 4: Play back audio
    if filename:
        input("\nPress Enter to play back the recorded audio...")
        play_test_audio(filename)
    
    # Test 5: Speech recognition
    print("\n" + "=" * 50)
    input("Press Enter to test speech recognition...")
    test_speech_recognition()
    
    # Test 6: Bible Clock integration
    test_bible_clock_voice()
    
    print("\n🎉 Microphone test completed!")
    print("\n📋 Summary:")
    print("- Check for ✅ marks indicating successful tests")
    print("- Fix any ❌ errors before using voice control")
    print("- ReSpeaker HAT should appear in device lists")
    print("- Audio recording should show volume bars when speaking")
    print("- Speech recognition should detect your words")

if __name__ == '__main__':
    main()