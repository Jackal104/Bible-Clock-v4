import logging
import os
import subprocess
import tempfile
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

# Override Piper audio output
def speak_with_piper_custom(text):
    model_path = os.path.expanduser("~/.local/share/piper/voices/en_US-amy-medium.onnx")
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_path = temp_file.name

      # Generate audio
      result = subprocess.run([
          'piper', '--model', model_path, '--output_file', temp_path
      ], input=text, text=True, capture_output=True)

      if result.returncode == 0:
          # Play with correct audio device
          subprocess.run(['aplay', '-D', 'plughw:1,0', temp_path])
          print(f"Said: {text}")

      os.unlink(temp_path)

# Test the voice system
speak_with_piper_custom("Bible Clock voice control is ready. Say Bible Clock to begin.")

from src.chatgpt_voice_control import ChatGPTPiperVoiceControl
from src.verse_manager import VerseManager

vm = VerseManager()
vc = ChatGPTPiperVoiceControl(vm, None, None)
vc._speak_with_piper = speak_with_piper_custom  # Override with working audio
vc.start_listening()

import time
print("Listening for 30 seconds... Say 'Bible Clock' then ask a question")
time.sleep(30)
