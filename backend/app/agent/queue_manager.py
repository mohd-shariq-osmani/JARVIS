import asyncio
import logging
from typing import Optional, Callable, Any, Dict

logger = logging.getLogger("MessageQueueManager")

class MessageQueueManager:
    """
    Manages sequential execution of incoming user requests (voice and text).
    Allows queuing multiple requests while executing, and provides instantaneous
    barge-in / abort when the user says "Stop Jarvis" or clicks Stop.
    """
    def __init__(self, agent, voice_manager, broadcast_callback: Optional[Callable] = None):
        self.agent = agent
        self.voice_manager = voice_manager
        self.broadcast_callback = broadcast_callback
        
        self.queue: asyncio.Queue = asyncio.Queue()
        self.current_task: Optional[asyncio.Task] = None
        self.worker_task: Optional[asyncio.Task] = None
        self.is_running = True
        self.active_request_id = 0

    def start(self):
        if not self.worker_task or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker_loop())
            logger.info("MessageQueueManager worker loop started.")

    async def enqueue(self, message: str, is_voice: bool = False) -> Dict[str, Any]:
        """
        Enqueues a user message or triggers immediate stop if the message is a stop command.
        """
        clean = message.lower().strip()
        
        # Immediate Stop / Interrupt check
        if clean in ["stop", "stop jarvis", "stop!", "jarvis stop", "quiet", "cancel", "shut up", "pause"]:
            logger.info(f"Stop command received: '{message}'. Halting everything.")
            await self.stop_all()
            return {"status": "stopped", "response": "Stopped."}

        # Normal message -> Push to queue
        req_id = self.active_request_id + 1
        self.active_request_id = req_id
        
        queue_size = self.queue.qsize()
        logger.info(f"Enqueuing message #{req_id} (queue depth: {queue_size}): '{message}'")
        
        # Notify UI of queued message if currently busy
        if self.voice_manager.is_speaking or self.current_task is not None:
            if self.broadcast_callback:
                await self.broadcast_callback({
                    "state": "QUEUED",
                    "transcript": message,
                    "queue_size": queue_size + 1
                })

        await self.queue.put((message, is_voice, req_id))
        return {"status": "queued", "position": queue_size + 1}

    async def stop_all(self):
        """
        Instantly halts TTS speech, cancels the active processing task,
        and purges all queued messages.
        """
        logger.info("STOP ALL triggered: Clearing queue and interrupting audio/agent.")
        
        # 1. Interrupt voice TTS audio immediately
        if self.voice_manager:
            self.voice_manager.interrupt()

        # 2. Clear all pending queued messages
        cleared_count = 0
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
                cleared_count += 1
            except (asyncio.QueueEmpty, ValueError):
                break

        if cleared_count > 0:
            logger.info(f"Purged {cleared_count} pending messages from queue.")

        # 3. Cancel currently running agent execution task
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            logger.info("Active agent processing task cancelled.")

        # 4. Notify frontend
        if self.broadcast_callback:
            await self.broadcast_callback({
                "state": "LISTENING" if getattr(self.voice_manager, "active_session", False) else "SLEEPING",
                "transcript": "[Stopped by user]"
            })

    async def _worker_loop(self):
        while self.is_running:
            try:
                message, is_voice, req_id = await self.queue.get()
                
                logger.info(f"Processing queued message #{req_id}: '{message}'")
                
                if self.broadcast_callback:
                    await self.broadcast_callback({
                        "state": "PROCESSING",
                        "transcript": message
                    })

                # Create cancellable task for agent execution
                self.current_task = asyncio.create_task(self.agent.handle_request(message))
                
                try:
                    response = await self.current_task
                    
                    if response and response != "[Stopped]":
                        logger.info(f"Agent response for #{req_id}: {response}")
                        
                        # Deliver response through voice if needed
                        if is_voice or getattr(self.voice_manager, "active_session", False):
                            await self.voice_manager.speak(response)
                        else:
                            # Update UI with text response
                            if self.broadcast_callback:
                                await self.broadcast_callback({
                                    "state": "READY",
                                    "transcript": response
                                })
                except asyncio.CancelledError:
                    logger.info(f"Task #{req_id} was cancelled during execution.")
                except Exception as e:
                    logger.error(f"Error handling queued request #{req_id}: {e}")
                finally:
                    self.current_task = None
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue worker loop error: {e}")
                await asyncio.sleep(0.1)
