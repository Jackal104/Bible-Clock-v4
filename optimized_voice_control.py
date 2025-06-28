from bible_clock_voice_complete import BibleClockVoiceSystem
import speech_recognition as sr
import time

class OptimizedVoiceControl(BibleClockVoiceSystem):
    def listen_for_wake_word(self):
        """Optimized wake word detection with reduced CPU usage."""
        print(f"Listening for wake word: '{self.wake_word}'")

        while self.listening:
            try:
                with self.microphone as source:
                    # Longer ambient noise adjustment
                    self.recognizer.adjust_for_ambient_noise(source, duration=1.0)

                    # Listen for wake word with longer timeout
                    audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=4)

                # Recognize speech
                try:
                    text = self.recognizer.recognize_google(audio).lower()
                    print(f"Heard: {text}")

                    if self.wake_word in text:
                        print(f"✅ Wake word detected!")
                        self.command_queue.put("wake_word_detected")

                except sr.UnknownValueError:
                    # Ignore unrecognized speech
                    pass
                except sr.RequestError as e:
                    print(f"Recognition service error: {e}")
                    time.sleep(1)

            except sr.WaitTimeoutError:
                # Normal timeout, continue listening
                pass
            except Exception as e:
                print(f"Listening error: {e}")
                time.sleep(0.5)  # Longer sleep on error

# Create and start optimized system
voice_system = OptimizedVoiceControl()
print("Starting optimized voice control...")
voice_system.speak_with_amy("Bible Clock voice control ready. Say Bible Clock to begin.")

threads = voice_system.start_listening()
if threads:
    print("\n🎤 Voice control active!")
    print(f"Say '{voice_system.wake_word}' followed by your command")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        voice_system.stop_listening()
        print("\nVoice control stopped.")
