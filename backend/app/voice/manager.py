import logging
import asyncio
import threading
import speech_recognition as sr
import os
import sys
import time
import subprocess

logger = logging.getLogger("VoiceManager")

class STTProvider:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    async def transcribe(self, audio_data) -> str:
        loop = asyncio.get_event_loop()
        try:
            text = await loop.run_in_executor(None, self.recognizer.recognize_google, audio_data)
            return text
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
                
                # Check for interruption every 50ms while playing
                while pygame.mixer.music.get_busy():
                    if self.interrupted:
                        pygame.mixer.music.stop()
                        break
                    time.sleep(0.05)
                    
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
        self.active_session = False
        self.queue_manager = None # Will be set on startup
        
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
            
    async def speak(self, text: str):
        self.is_speaking = True
        await self.set_state("SPEAKING", text)
        logger.info(f"Voice Manager Speaking: {text}")
        await self.tts.synthesize(text)
        
        self.is_speaking = False
        self.last_speak_end = time.time()
        
        await self.set_state("LISTENING" if self.active_session else "SLEEPING")

    def _listen_loop_sync(self, loop):
        with sr.Microphone() as source:
            self.stt.recognizer.energy_threshold = 300
            self.stt.recognizer.dynamic_energy_threshold = False
            logger.info("Voice Manager: Hardware Ready. Listening for speech / wake word...")
            
            self.active_session = False
            
            while self.listening:
                try:
                    # Update state in UI if idle
                    if not self.is_speaking and self.state not in ["PROCESSING", "QUEUED"]:
                        target_state = "LISTENING" if self.active_session else "SLEEPING"
                        if self.state != target_state:
                            asyncio.run_coroutine_threadsafe(self.set_state(target_state), loop)
                        
                    # Listen continuously (allows barge-in even while speaking)
                    audio = self.stt.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    
                    try:
                        text = self.stt.recognizer.recognize_google(audio).lower().strip()
                        if not text:
                            continue
                            
                        logger.info(f"[STT Heard]: '{text}' (is_speaking={self.is_speaking})")
                        
                        # Check for Stop / Barge-in trigger
                        if "stop jarvis" in text or text in ["stop", "stop!", "jarvis stop", "quiet", "cancel", "shut up"]:
                            logger.info("Barge-in STOP detected.")
                            self.interrupt()
                            if self.queue_manager:
                                asyncio.run_coroutine_threadsafe(self.queue_manager.stop_all(), loop)
                            self.active_session = False
                            asyncio.run_coroutine_threadsafe(self.set_state("SLEEPING", transcript="Stopped. Going back to sleep."), loop)
                            continue

                        # Check session activation
                        if not self.active_session:
                            if self.wake_word in text:
                                self.active_session = True
                                logger.info("Session Activated by Wake Word")
                                asyncio.run_coroutine_threadsafe(self.set_state("LISTENING", transcript="JARVIS activated. I am listening..."), loop)
                                
                                # Extract command if spoken in same breath
                                command = text.split(self.wake_word)[-1].strip()
                                if command:
                                    if self.queue_manager:
                                        asyncio.run_coroutine_threadsafe(self.queue_manager.enqueue(command, is_voice=True), loop)
                        else:
                            # User is in active session
                            if "thank you jarvis" in text or "bye jarvis" in text or "goodbye jarvis" in text:
                                self.active_session = False
                                logger.info("Session Deactivated")
                                self.interrupt()
                                asyncio.run_coroutine_threadsafe(self.set_state("SLEEPING", transcript="Goodbye, sir."), loop)
                            else:
                                command = text.strip()
                                if command:
                                    if self.is_speaking:
                                        # User spoke while JARVIS was speaking -> barge in or queue
                                        logger.info(f"User spoke while speaking: '{command}'")
                                    if self.queue_manager:
                                        asyncio.run_coroutine_threadsafe(self.queue_manager.enqueue(command, is_voice=True), loop)
                                        
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
