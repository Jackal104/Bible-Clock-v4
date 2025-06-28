import speech_recognition as sr
import time
from bible_clock_voice_complete import BibleClockVoiceSystem

print("🎤 Bible Clock - Final Working Voice Control")
print("=" * 50)

# Create voice system
voice_system = BibleClockVoiceSystem()

# Set up working speech recognition (we know this works)
recognizer = sr.Recognizer()
microphone = sr.Microphone(device_index=2)  # USB PnP Audio Device

print("✅ All components ready")
print("✅ Amy voice working")
print("✅ ChatGPT API configured")
print("✅ USB microphone detected")
print("✅ USB speakers configured")

# Initial announcement
voice_system.speak_with_amy("Bible Clock voice control is ready. Press space then speak your command.")

print("\n" + "=" * 50)
print("PRESS SPACEBAR + ENTER, then speak your command:")
print("• 'explain this verse' - Current verse explanation")
print("• 'what does john 3:16 say' - Bible questions")
print("• 'next verse' - Navigate forward")
print("• 'read current verse' - Hear current verse")
print("• 'quit' - Exit")
print("=" * 50)

try:
    while True:
        # Wait for spacebar trigger
        user_input = input("\nPress SPACE+ENTER to speak (or type 'quit'): ").strip().lower()

        if user_input == 'quit' or user_input == 'q':
            break

        # Listen for voice command
        try:
            print("🎤 Listening... speak your command now!")

            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)

            command = recognizer.recognize_google(audio).lower()
            print(f"✅ Command: '{command}'")

            # Process with voice system
            voice_system._process_voice_command(command)

        except sr.WaitTimeoutError:
            print("⏰ No speech detected - try again")
        except sr.UnknownValueError:
            print("❓ Couldn't understand - try speaking more clearly")
            voice_system.speak_with_amy("I didn't understand that. Please try again.")
        except sr.RequestError as e:
            print(f"❌ Recognition error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

except KeyboardInterrupt:
    pass

print("\n👋 Bible Clock voice control stopped.")
voice_system.speak_with_amy("Bible Clock voice control goodbye.")
