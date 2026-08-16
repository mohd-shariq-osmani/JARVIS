import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.agent.queue_manager import MessageQueueManager

class MockAgent:
    def __init__(self):
        self.processed = []

    async def handle_request(self, message: str):
        await asyncio.sleep(0.1) # Simulate execution work
        self.processed.append(message)
        return f"Done: {message}"

class MockVoiceManager:
    def __init__(self):
        self.is_speaking = False
        self.interrupted = False
        self.active_session = False

    def interrupt(self):
        self.interrupted = True
        self.is_speaking = False

    async def speak(self, text: str):
        self.is_speaking = True
        await asyncio.sleep(0.1)
        self.is_speaking = False

async def test_queue_and_interrupt():
    print("=== 1. Testing Sequential Queue Execution ===")
    agent = MockAgent()
    voice = MockVoiceManager()
    
    queue = MessageQueueManager(agent, voice)
    queue.start()

    # Enqueue 3 messages in rapid succession
    await queue.enqueue("Message 1")
    await queue.enqueue("Message 2")
    await queue.enqueue("Message 3")

    # Wait for worker to finish processing all 3
    await asyncio.sleep(0.5)

    print("Processed messages:", agent.processed)
    assert agent.processed == ["Message 1", "Message 2", "Message 3"]

    print("=== 2. Testing Instant Stop & Queue Purge ===")
    # Enqueue multiple long-running messages
    await queue.enqueue("Message 4")
    await queue.enqueue("Message 5")
    await queue.enqueue("Message 6")

    # Send Stop Jarvis immediately
    stop_res = await queue.enqueue("Stop Jarvis")
    print("Stop response:", stop_res)
    assert stop_res["status"] == "stopped"
    assert voice.interrupted is True

    # Allow worker loop to settle
    await asyncio.sleep(0.2)
    print("Final processed messages after stop:", agent.processed)
    assert "Message 6" not in agent.processed

    queue.is_running = False
    if queue.worker_task:
        queue.worker_task.cancel()

    print("\n ALL QUEUE & INTERRUPT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_queue_and_interrupt())
