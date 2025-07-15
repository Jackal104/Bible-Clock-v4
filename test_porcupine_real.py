import os
import numpy as np
import pyaudio
import pvporcupine
from bible_clock_voice_complete import BibleClockVoiceSystem

# Use your actual Porcupine configuration
PORCUPINE_ACCESS_KEY = os.getenv('PORCUPINE_ACCESS_KEY',
'/kTtNAdQAezXSkk+Oqm6snnKpGlAB2MxKrndyF1SqFoNsoIvEo2Yfw==')
KEYWORD_PATH = os.getenv('PORCUPINE_KEYWORD_PATH',
'/home/admin/Bible-Clock-v3/Bible-Clock_en_raspberry-pi_v3_0_0.ppn')

print("🎤 Testing your actual Porcupine setup")
print(f"Keyword file: {KEYWORD_PATH}")
print(f"Access key: {PORCUPINE_ACCESS_KEY[:20]}...")

# Initialize voice system for responses
voice_system = BibleClockVoiceSystem()

try:
    # Initialize Porcupine with your custom keyword
    porcupine = pvporcupine.create(
        access_key=PORCUPINE_ACCESS_KEY,
        keyword_paths=[KEYWORD_PATH],
        sensitivities=[0.5]
    )

    # Initialize PyAudio
    pa = pyaudio.PyAudio()

    # Use USB microphone (device 2)
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        input_device_index=2,
        frames_per_buffer=porcupine.frame_length
    )

    print(f"✅ Porcupine initialized")
    print(f"Sample rate: {porcupine.sample_rate}")
    print(f"Frame length: {porcupine.frame_length}")
    print("\n🎤 Say 'Bible Clock' to trigger...")

    voice_system.speak_with_amy("Bible Clock with Porcupine ready. Say Bible Clock to begin.")

    while True:
        # Read audio
        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = np.frombuffer(pcm, dtype=np.int16)

        # Process with Porcupine
        keyword_index = porcupine.process(pcm)

        if keyword_index >= 0:
            print("🎯 BIBLE CLOCK detected by Porcupine!")
            voice_system.speak_with_amy("Yes, how can I help you?")

            # Now listen for command with speech recognition
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            microphone = sr.Microphone(device_index=2)

            try:
                print("Listening for command...")
                with microphone as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)

                command = recognizer.recognize_google(audio).lower()
                print(f"Command: '{command}'")
                voice_system._process_voice_command(command)

            except Exception as e:
                print(f"Command recognition error: {e}")
                voice_system.speak_with_amy("I didn't understand that command.")

except KeyboardInterrupt:
    print("\nStopping...")
finally:
    if 'audio_stream' in locals():
        audio_stream.close()
    if 'pa' in locals():
        pa.terminate()
    if 'porcupine' in locals():
        porcupine.delete()
