# Voice Control Fixes for USB Audio Devices

This document describes the fixes implemented to resolve PyAudio microphone initialization issues with USB audio devices on Raspberry Pi.

## Problem Solved

The voice control system was failing with these errors:
```
Expression 'parameters->channelCount <= maxChans' failed in 'src/hostapi/alsa/pa_linux_alsa.c'
Listening error: 'NoneType' object has no attribute 'close'
```

This occurred because PyAudio was trying to initialize USB microphones with hardcoded parameters that weren't compatible with the device capabilities.

## Solution Implemented

### 1. Enhanced USB Microphone Initialization (`src/voice_control.py`)

The `_initialize_usb_microphone()` method now:

- **Detects device capabilities**: Queries PyAudio for max channels and sample rate
- **Uses safe parameters**: Automatically selects mono (1 channel) and appropriate sample rate
- **Handles ALSA hardware IDs**: Supports both device names and `hw:X,Y` format
- **Tests initialization**: Verifies microphone works before returning
- **Graceful fallback**: Falls back to default microphone if USB device fails

### 2. Improved Device Detection

The system now searches for USB audio devices using multiple methods:
- Direct device name matching (`USB PnP Audio Device`)
- Hardware ID matching (`hw:2,0` → `card 2`)
- Generic USB device detection (`usb`, `fifine`, `audio device`)

### 3. Parameter Validation

Before creating the microphone object, the system:
- Queries device capabilities using `pyaudio.get_device_info_by_index()`
- Sets channels to `min(1, max_input_channels)` for mono recording
- Chooses sample rate: 16kHz if supported, otherwise 8kHz
- Uses standard chunk size of 1024 samples

## Testing

Run the test script to verify the fixes:
```bash
python test_voice_fixes.py
```

This will test:
- Voice control initialization
- USB microphone access
- TTS engine setup
- Command processing
- Listening state management

## Configuration

The `.env` file should have:
```
ENABLE_VOICE=true
USB_AUDIO_ENABLED=true
USB_MIC_DEVICE_NAME="USB PnP Audio Device"
USB_SPEAKER_DEVICE_NAME="USB PnP Audio Device"
AUDIO_INPUT_ENABLED=true
AUDIO_OUTPUT_ENABLED=true
```

## Usage

1. **Start the application**:
   ```bash
   ./start_bible_clock.sh
   ```

2. **Test wake word detection**:
   Say "Bible Clock, help" near the microphone

3. **Verify TTS output**:
   Listen for spoken responses through USB speakers

## Hardware Compatibility

These fixes support:
- **Fifine K053 USB Microphone**
- **USB-powered speakers** (Logitech Z120, etc.)
- **Generic USB audio devices**
- **ALSA hardware addressing** (`hw:X,Y` format)

## Troubleshooting

If voice control still doesn't work:

1. **Check device detection**:
   ```python
   import speech_recognition as sr
   print(sr.Microphone.list_microphone_names())
   ```

2. **Test hardware directly**:
   ```bash
   arecord -D hw:2,0 -f S16_LE -r 16000 -c 1 test.wav
   aplay -D hw:1,0 test.wav
   ```

3. **Check logs**: Look for detailed initialization messages in the application logs

## Technical Details

The fixes address the root cause: PyAudio's parameter validation requires that the requested parameters match the device's actual capabilities. The enhanced initialization:

1. Queries the device for its maximum input channels
2. Uses the minimum of requested channels (1) and device capability
3. Selects an appropriate sample rate based on device defaults
4. Tests the configuration before use
5. Provides detailed logging for debugging

This ensures compatibility with a wide range of USB audio devices while maintaining optimal performance for voice recognition.