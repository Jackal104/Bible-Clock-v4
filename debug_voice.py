import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

print("Environment check:")
print("ENABLE_CHATGPT_VOICE:", os.getenv('ENABLE_CHATGPT_VOICE'))
print("OPENAI_API_KEY set:", bool(os.getenv('OPENAI_API_KEY')))
print("PIPER_VOICE_MODEL:", os.getenv('PIPER_VOICE_MODEL'))

from src.chatgpt_voice_control import ChatGPTPiperVoiceControl
from src.verse_manager import VerseManager

vm = VerseManager()
vc = ChatGPTPiperVoiceControl(vm, None, None)
print("Starting voice control...")
vc.start_listening()

import time
print("Listening for 20 seconds...")
time.sleep(20)
