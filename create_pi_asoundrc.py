#!/usr/bin/env python3
"""
Create .asoundrc file for Bible Clock on Raspberry Pi
This script creates the proper ALSA configuration for:
- Card 1: USB PnP Audio Device (microphone)
- Card 2: UACDemoV1.0 (USB speaker)
"""

import os
import subprocess

def create_asoundrc():
    """Create .asoundrc file with proper audio configuration."""
    
    content = """# Bible Clock Audio Configuration
# Card 1: USB PnP Audio Device (microphone)  
# Card 2: UACDemoV1.0 (USB speaker)

pcm.!default {
    type asym
    playback.pcm "usb_speaker_output"
    capture.pcm "usb_mic_input"
}

pcm.usb_mic_input {
    type plug
    slave {
        pcm "hw:1,0"
        rate 48000
        channels 1
        format S16_LE
    }
}

pcm.usb_speaker_output {
    type plug
    slave {
        pcm "hw:2,0"
        rate 44100
        channels 2
        format S16_LE
    }
}

ctl.!default {
    type hw
    card 2
}

pcm.microphone {
    type plug
    slave.pcm "usb_mic_input"
}

pcm.speakers {
    type plug
    slave.pcm "usb_speaker_output"
}

# Additional named devices for Porcupine compatibility
pcm.fifine_input {
    type plug
    slave.pcm "usb_mic_input"
}

pcm.usb_speaker_output {
    type plug
    slave.pcm "usb_speaker_output"
}
"""

    asoundrc_path = os.path.expanduser('~/.asoundrc')
    
    try:
        # Backup existing file if it exists
        if os.path.exists(asoundrc_path):
            backup_path = f"{asoundrc_path}.backup"
            os.rename(asoundrc_path, backup_path)
            print(f"✅ Backed up existing .asoundrc to {backup_path}")
        
        # Write new configuration
        with open(asoundrc_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Created .asoundrc at {asoundrc_path}")
        
        # Test the configuration
        print("\n🧪 Testing audio configuration...")
        
        # Test if cards are detected
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Audio capture devices detected")
        else:
            print(f"⚠️ Audio capture test: {result.stderr}")
        
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Audio playback devices detected")
        else:
            print(f"⚠️ Audio playback test: {result.stderr}")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .asoundrc: {e}")
        return False

def show_current_devices():
    """Show current audio devices."""
    print("\n📱 Current Audio Devices:")
    
    try:
        # Show cards
        with open('/proc/asound/cards', 'r') as f:
            cards = f.read()
        print("ALSA Cards:")
        print(cards)
        
        # Show USB devices
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        if result.returncode == 0:
            usb_audio = [line for line in result.stdout.split('\n') if 'audio' in line.lower()]
            if usb_audio:
                print("USB Audio Devices:")
                for device in usb_audio:
                    print(f"  {device}")
    
    except Exception as e:
        print(f"⚠️ Could not read device information: {e}")

if __name__ == '__main__':
    print("🎵 Bible Clock ALSA Configuration Setup")
    print("=" * 50)
    
    show_current_devices()
    
    if create_asoundrc():
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Test audio: arecord -D microphone -f S16_LE -r 48000 -c 1 -d 2 test.wav")
        print("2. Test playback: aplay -D speakers test.wav")
        print("3. Install Porcupine: python3 install_porcupine.py")
        print("4. Start Bible Clock: ./start_bible_clock.sh")
    else:
        print("\n❌ Setup failed")