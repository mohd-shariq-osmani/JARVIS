import os
import sys
import subprocess

bin_path = os.path.join(os.path.dirname(sys.executable), 'edge-tts.exe')
temp_audio = os.path.join(os.path.dirname(__file__), "temp_tts.mp3")

if os.path.exists(temp_audio):
    os.remove(temp_audio)

print("Running subprocess.run...")
subprocess.run([bin_path, "--voice", "en-US-AriaNeural", "--text", "Hello", "--write-media", temp_audio])

print(f"Audio file created: {os.path.exists(temp_audio)}")

if os.path.exists(temp_audio):
    import pygame
    import time
    pygame.mixer.init()
    pygame.mixer.music.load(temp_audio)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    print("Played successfully.")
