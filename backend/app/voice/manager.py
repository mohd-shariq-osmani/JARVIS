import logging
import asyncio
import threading
import speech_recognition as sr
import os
import sys
import time
import subprocess
from typing import Optional

logger = logging.getLogger("VoiceManager")

import re

def normalize_spoken_text(text: str) -> str:
    """Normalizes spoken transcriptions, converting spoken times and fixing misheard commands."""
    if not text:
        return ""
    t = text.lower().strip()
    
    # Fix common STT phonetic confusions
    t = re.sub(r'\bopen fire (?:the )?\b', 'open ', t)
    t = re.sub(r'\bopen for me (?:the )?\b', 'open ', t)
    
    # Normalize p.m. -> PM, a.m. -> AM
    t = re.sub(r'\bp\.?m\.?\b', 'PM', t, flags=re.IGNORECASE)
    t = re.sub(r'\ba\.?m\.?\b', 'AM', t, flags=re.IGNORECASE)
    # 3-digit: '145 PM' -> '1:45 PM', '930 AM' -> '9:30 AM'
    t = re.sub(r'\b([1-9])([0-5][0-9])\s*(AM|PM)\b', r'\1:\2 \3', t, flags=re.IGNORECASE)
    # 4-digit: '1045 PM' -> '10:45 PM', '1130 AM' -> '11:30 AM', '1245 PM' -> '12:45 PM'
    t = re.sub(r'\b(1[0-2])([0-5][0-9])\s*(AM|PM)\b', r'\1:\2 \3', t, flags=re.IGNORECASE)
    return t.strip()

class STTProvider:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    async def transcribe(self, audio_data) -> str:
        loop = asyncio.get_event_loop()
        try:
            raw_text = await loop.run_in_executor(None, self.recognizer.recognize_google, audio_data)
            return normalize_spoken_text(raw_text)
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            logger.error(f"STT Error: {e}")
            return ""

class EdgeTTSProvider:
    def __init__(self):
        logger.info("Initializing Edge-TTS...")
        import pygame
        pygame.mixer.init()
        self.interrupted = False
        logger.info("Edge-TTS and PyGame mixer initialized.")
        
    def stop(self):
        """Immediately halts any active audio playback."""
        self.interrupted = True
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                try:
                    pygame.mixer.music.unload()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error stopping mixer: {e}")

    def _speak_sync(self, text: str):
        self.interrupted = False
        try:
            import pygame
            temp_audio = os.path.join(os.path.dirname(__file__), "temp_tts.mp3")
            
            # Generate audio using Edge-TTS CLI
            safe_text = text.replace('"', '').replace("'", "")
            edge_tts_bin = os.path.join(os.path.dirname(sys.executable), 'edge-tts.exe')
            
            subprocess.run([edge_tts_bin, "--voice", "en-US-AriaNeural", "--text", safe_text, "--write-media", temp_audio])
            
            if self.interrupted:
                return

            if os.path.exists(temp_audio):
                pygame.mixer.music.load(temp_audio)
                pygame.mixer.music.play()
                
                # Check for interruption every 40ms while playing
                while pygame.mixer.music.get_busy():
                    if self.interrupted:
                        pygame.mixer.music.stop()
                        break
                    time.sleep(0.04)
                    
                try:
                    pygame.mixer.music.unload()
                    os.remove(temp_audio)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Edge-TTS playback error: {e}")

    async def synthesize(self, text: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._speak_sync, text)

class VoiceManager:
    def __init__(self):
        self.state = "SLEEPING"
        self.wake_word = "jarvis"
        self.stt = STTProvider()
        self.tts = EdgeTTSProvider()
        self.listening = False
        self.state_callback = None
        self.is_speaking = False
        self.last_speak_end = 0
        self.last_spoken_text = ""
        self.active_session = False
        self.last_active_time = 0
        self.session_timeout = 25.0  # Keep listening for 25 seconds of silence
        self.queue_manager = None
        
    def set_queue_manager(self, queue_manager):
        self.queue_manager = queue_manager

    def interrupt(self):
        """Instantly stops speech playback and resets speaking state."""
        logger.info("VoiceManager: Interrupting speech playback.")
        self.is_speaking = False
        self.tts.stop()

    async def set_state(self, state: str, transcript: str = None):
        self.state = state
        logger.info(f"Voice State: {state}")
        if self.state_callback:
            await self.state_callback(state, transcript)
            
    def _clean_tts_speech(self, text: str) -> str:
        """Cleans filepaths, code symbols, and long filenames so spoken speech is natural and elegant."""
        if not text:
            return ""
        # Remove code blocks / backticks
        t = re.sub(r'[`\'"]+([^`\'"]+)[`\'"]+', r'\1', text)
        # Strip full file paths (e.g. C:\Users\...\file.png)
        t = re.sub(r'[a-zA-Z]:[\\/][^\s]+[\\/]([^\s\\/]+)', r'\1', t)
        # Replace long auto-generated filenames
        t = re.sub(r'(?i)\bScreenshot[_\d-]*\.(?:png|jpg|jpeg)\b', 'the screenshot', t)
        # Strip long hashes/hex strings
        t = re.sub(r'\b[0-9a-fA-F]{8,}\b', '', t)
        return t.strip()

    async def speak(self, text: str):
        self.is_speaking = True
        self.last_spoken_text = text.lower()
        await self.set_state("SPEAKING", text)
        logger.info(f"Voice Manager Speaking: {text}")
        
        spoken_text = self._clean_tts_speech(text)
        await self.tts.synthesize(spoken_text)
        
        self.is_speaking = False
        self.last_speak_end = time.time()
        self.last_active_time = time.time()
        
        # Keep session active in continuous listening mode!
        self.active_session = True
        await self.set_state("LISTENING")

    def _listen_loop_sync(self, loop):
        with sr.Microphone() as source:
            self.stt.recognizer.energy_threshold = 300
            self.stt.recognizer.dynamic_energy_threshold = False
            logger.info("Voice Manager: Hardware Ready. Listening for speech / wake word...")
            
            self.active_session = False
            
            while self.listening:
                try:
                    now = time.time()
                    
                    # Check for continuous conversation timeout (25s of inactivity)
                    if self.active_session and not self.is_speaking:
                        if now - self.last_active_time > self.session_timeout:
                            logger.info(f"Active conversation session timed out after {self.session_timeout}s. Entering SLEEPING.")
                            self.active_session = False
                            asyncio.run_coroutine_threadsafe(self.set_state("SLEEPING"), loop)

                    # Update state in UI if idle
                    if not self.is_speaking and self.state not in ["PROCESSING", "QUEUED"]:
                        target_state = "LISTENING" if self.active_session else "SLEEPING"
                        if self.state != target_state:
                            asyncio.run_coroutine_threadsafe(self.set_state(target_state), loop)
                        
                    # Listen for incoming voice input
                    audio = self.stt.recognizer.listen(source, timeout=1, phrase_time_limit=8)
                    
                    try:
                        text = self.stt.recognizer.recognize_google(audio).lower().strip()
                        if not text:
                            continue
                            
                        logger.info(f"[STT Heard]: '{text}' (active_session={self.active_session}, is_speaking={self.is_speaking})")
                        
                        # Discard speaker echo / acoustic feedback during or immediately after speech
                        if self.is_speaking or (time.time() - self.last_speak_end < 2.0):
                            logger.info(f"Discarding acoustic feedback during/after speech: '{text}'")
                            continue

                        # Discard self-echo if recognized words match what JARVIS just spoke
                        if self.last_spoken_text and (text in self.last_spoken_text or self.last_spoken_text in text):
                            logger.info(f"Discarding recognized echo of TTS output: '{text}'")
                            continue

                        # Stop / Barge-in trigger checks
                        is_stop_command = (
                            "stop jarvis" in text or 
                            text in ["stop", "stop!", "jarvis stop", "quiet", "cancel", "shut up", "halt"]
                        )
                        
                        if is_stop_command:
                            logger.info("Barge-in STOP detected.")
                            self.interrupt()
                            if self.queue_manager:
                                asyncio.run_coroutine_threadsafe(self.queue_manager.stop_all(), loop)
                            self.active_session = False
                            asyncio.run_coroutine_threadsafe(self.set_state("SLEEPING", transcript="Stopped. Going back to sleep."), loop)
                            continue

                        # Check if user is responding to an active Access/Permission authorization request
                        try:
                            from app.security.access_manager import access_manager
                            if access_manager._future_responses:
                                voice_decision = access_manager.handle_voice_permission(text)
                                if voice_decision is not None:
                                    msg = "Authorization granted, sir." if voice_decision else "Access denied, sir."
                                    asyncio.run_coroutine_threadsafe(self.speak(msg), loop)
                                    continue
                        except Exception as e:
                            logger.error(f"Voice permission error: {e}")

                        # Active Conversation Mode (No need to say JARVIS every time!)
                        if self.active_session:
                            self.last_active_time = time.time()
                            
                            # Check for conversation ending phrases
                            if any(k in text for k in ["thank you", "thanks jarvis", "bye jarvis", "goodbye", "nevermind", "that is all", "thats all", "go to sleep"]):
                                self.active_session = False
                                logger.info("Session Deactivated by user polite exit.")
                                self.interrupt()
                                asyncio.run_coroutine_threadsafe(self.set_state("SLEEPING", transcript="Standing by, sir."), loop)
                            else:
                                # Strip "jarvis" prefix if user happened to say it anyway
                                clean_cmd = text.replace("jarvis", "").strip()
                                if not clean_cmd:
                                    clean_cmd = text.strip()
                                    
                                if clean_cmd and len(clean_cmd) > 2:
                                    logger.info(f"Active session command accepted: '{clean_cmd}'")
                                    if self.queue_manager:
                                        asyncio.run_coroutine_threadsafe(self.queue_manager.enqueue(clean_cmd, is_voice=True), loop)
                        else:
                            # Sleeping mode: Wake up on "jarvis"
                            if self.wake_word in text:
                                self.active_session = True
                                self.last_active_time = time.time()
                                logger.info("Session Activated by Wake Word")
                                
                                # Extract command if spoken after wake word
                                command = text.split(self.wake_word)[-1].strip()
                                if command and len(command) > 2:
                                    if self.queue_manager:
                                        asyncio.run_coroutine_threadsafe(self.queue_manager.enqueue(command, is_voice=True), loop)
                                else:
                                    asyncio.run_coroutine_threadsafe(self.set_state("LISTENING", transcript="JARVIS activated. I am listening..."), loop)
                                        
                    except sr.UnknownValueError:
                        pass
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Listen loop iteration error: {e}")
                    time.sleep(0.1)

    def start_listening(self, state_callback=None):
        if not self.listening:
            self.listening = True
            self.state_callback = state_callback
            loop = asyncio.get_event_loop()
            thread = threading.Thread(target=self._listen_loop_sync, args=(loop,), daemon=True)
            thread.start()
            
    def stop_listening(self):
        self.listening = False
        self.interrupt()
