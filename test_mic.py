  import speech_recognition as sr
  r = sr.Recognizer()
  m = sr.Microphone()
  print('Listening for 5 seconds - say something...')
  with m as source:
      audio = r.listen(source, timeout=10)
  try:
      text = r.recognize_google(audio)
      print(f'You said: {text}')
  except Exception as e:
      print(f'Recognition error: {e}')
  EOF
