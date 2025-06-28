#!/usr/bin/env python3
"""Debug script to check how the OpenAI API key is being loaded."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv('OPENAI_API_KEY', '')

print(f"API key length: {len(api_key)}")
print(f"API key repr: {repr(api_key)}")
print(f"Contains newline: {chr(10) in api_key}")
print(f"Contains carriage return: {chr(13) in api_key}")
print(f"First 20 chars: {repr(api_key[:20])}")
print(f"Last 20 chars: {repr(api_key[-20:])}")

# Check for any whitespace issues
cleaned_key = api_key.strip()
print(f"Length after strip: {len(cleaned_key)}")
print(f"Keys are equal: {api_key == cleaned_key}")