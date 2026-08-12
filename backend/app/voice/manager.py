import logging
import asyncio
import threading
import speech_recognition as sr

logger = logging.getLogger("VoiceManager")

class STTProvider:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    async def transcribe(self, audio_data) -> str:
        # We need to offload the blocking recognition to a thread
        loop = asyncio.get_event_loop()
        try:
            # Using google STT as a stand-in for local STT if missing offline sphinx.
            # In a true local setup, this would be `recognize_sphinx` or `whisper`.
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
        logger.info("Edge-TTS and PyGame mixer initialized.")
        
    def _speak_sync(self, text: str):
        try:
            import os
            import sys
            import pygame
            import time
            import subprocess
            temp_audio = os.path.join(os.path.dirname(__file__), "temp_tts.mp3")
            
            # Generate audio using Edge-TTS CLI
            safe_text = text.replace('"', '').replace("'", "")
            edge_tts_bin = os.path.join(os.path.dirname(sys.executable), 'edge-tts.exe')
            
            subprocess.run([edge_tts_bin, "--voice", "en-US-AriaNeural", "--text", safe_text, "--write-media", temp_audio])
            
            if os.path.exists(temp_audio):
                pygame.mixer.music.load(temp_audio)
                pygame.mixer.music.play()
                
                # Wait until audio finishes playing
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                    
                # Unload so we can overwrite next time
                pygame.mixer.music.unload()
                try:
                    os.remove(temp_audio)
                except:
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
        
        import time
        self.is_speaking = False
        self.last_speak_end = time.time()
        
        await self.set_state("LISTENING" if self.active_session else "SLEEPING")

    def _listen_loop_sync(self, orchestrator_callback, loop):
        with sr.Microphone() as source:
            self.stt.recognizer.energy_threshold = 300
            self.stt.recognizer.dynamic_energy_threshold = False
            logger.info("Voice Manager: Hardware Ready. Listening for wake word...")
            
            self.active_session = False
            
            while self.listening:
                import time
                if self.is_speaking:
                    time.sleep(0.2)
                    continue
                    
                try:
                    target_state = "LISTENING" if self.active_session else "SLEEPING"
                    if self.state != target_state and self.state != "PROCESSING" and not self.is_speaking:
                        asyncio.run_coroutine_threadsafe(self.set_state(target_state), loop)
                        
                    audio = self.stt.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    
                    # Ignore anything heard if we are speaking or just finished speaking
                    if self.is_speaking or (time.time() - self.last_speak_end < 2.0):
                        continue
                    
                    if self.state != "PROCESSING" and not self.is_speaking:
                        asyncio.run_coroutine_threadsafe(self.set_state("PROCESSING"), loop)
                    
                    try:
                        text = self.stt.recognizer.recognize_google(audio).lower()
                        logger.info(f"[STT Heard]: {text}")
                        
                        if not self.active_session:
                            if self.wake_word in text:
                                self.active_session = True
                                logger.info("Session Activated")
                                asyncio.run_coroutine_threadsafe(self.set_state("LISTENING", transcript="JARVIS activated. I am listening..."), loop)
                                
                                # Process command if spoken in same breath
                                command = text.split(self.wake_word)[-1].strip()
                                if command:
                                    asyncio.run_coroutine_threadsafe(self.set_state("PROCESSING", transcript=command), loop)
                                    asyncio.run_coroutine_threadsafe(orchestrator_callback(command), loop)
                        else:
                            if "stop jarvis" in text or "thank you jarvis" in text:
                                self.active_session = False
                                logger.info("Session Deactivated")
                                asyncio.run_coroutine_threadsafe(self.set_state("SLEEPING", transcript="Going back to sleep."), loop)
                            else:
                                command = text.strip()
                                if command:
                                    asyncio.run_coroutine_threadsafe(self.set_state("PROCESSING", transcript=command), loop)
                                    asyncio.run_coroutine_threadsafe(orchestrator_callback(command), loop)
                    except sr.UnknownValueError:
                        # Reset state if nothing recognized
                        target_state = "LISTENING" if self.active_session else "SLEEPING"
                        asyncio.run_coroutine_threadsafe(self.set_state(target_state), loop)
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Listen loop error: {e}")

    def start_listening(self, orchestrator_callback, state_callback=None):
        if not self.listening:
            self.listening = True
            self.state_callback = state_callback
            loop = asyncio.get_event_loop()
            thread = threading.Thread(target=self._listen_loop_sync, args=(orchestrator_callback, loop), daemon=True)
            thread.start()
            
    def stop_listening(self):
        self.listening = False
