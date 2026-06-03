import logging
import os
import json
import httpx
from typing import Any
from datetime import datetime

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    function_tool,
    RunContext,
)
from livekit.plugins import silero, openai
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

class Assistant(Agent):
    def __init__(self, webhook_url: str = None, webhook_enabled: bool = False) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant. The user is interacting with you via voice, even if you perceive the conversation as text.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.""",
        )
        self.webhook_url = webhook_url
        self.webhook_enabled = webhook_enabled
        self.conversation_history = []

    @function_tool()
    async def multiply_numbers(
        self,
        context: RunContext,
        number1: int,
        number2: int,
    ) -> dict[str, Any]:
        """Multiply two numbers.
        
        Args:
            number1: The first number to multiply.
            number2: The second number to multiply.
        """
        return f"The product of {number1} and {number2} is {number1 * number2}."

    @function_tool()
    async def delegate_to_agent(
        self,
        context: RunContext,
        reason: str,
    ) -> dict[str, Any]:
        """Delegate the conversation to another agent via webhook.
        
        Args:
            reason: The reason for delegating this conversation.
        """
        if not self.webhook_enabled or not self.webhook_url:
            return {
                "success": False,
                "error": "Webhook delegation is not enabled"
            }
        
        try:
            payload = {
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "conversation_history": self.conversation_history,
                "room_name": context.room.name if hasattr(context, 'room') else None,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=float(os.getenv("WEBHOOK_TIMEOUT", "30"))
                )
                response.raise_for_status()
                
                logger.info(f"Successfully delegated to webhook: {self.webhook_url}")
                return {
                    "success": True,
                    "message": f"Conversation delegated to {self.webhook_url}",
                    "response_status": response.status_code
                }
        except Exception as e:
            logger.error(f"Error delegating to webhook: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # LLM Configuration
    llama_model = os.getenv("LLAMA_MODEL", "qwen3-4b")
    llama_base_url = os.getenv("LLAMA_BASE_URL", "http://10.0.0.3:8000/v1")

    # STT Configuration
    stt_provider = os.getenv("STT_PROVIDER", "nemotron").lower()
    stt_base_url = os.getenv("STT_BASE_URL", "http://10.0.0.3:8000/v1")
    stt_model = os.getenv("STT_MODEL", "nemotron-speech-streaming")
    stt_api_key = os.getenv("STT_API_KEY", "no-key-needed")

    # TTS Configuration
    tts_base_url = os.getenv("TTS_BASE_URL", "http://10.0.0.3:8880/v1")
    tts_model = os.getenv("TTS_MODEL", "kokoro")
    tts_voice = os.getenv("TTS_VOICE", "af_nova")

    # Webhook Configuration
    webhook_url = os.getenv("WEBHOOK_URL")
    webhook_enabled = os.getenv("WEBHOOK_ENABLED", "true").lower() == "true"

    logger.info(
        "Starting agent with:"
        "\n  STT provider=%s, base_url=%s, model=%s"
        "\n  LLM base_url=%s, model=%s"
        "\n  TTS base_url=%s, model=%s, voice=%s"
        "\n  Webhook enabled=%s, url=%s",
        stt_provider,
        stt_base_url,
        stt_model,
        llama_base_url,
        llama_model,
        tts_base_url,
        tts_model,
        tts_voice,
        webhook_enabled,
        webhook_url,
    )

    session = AgentSession(
        stt=openai.STT(
            base_url=stt_base_url,
            model=stt_model,
            api_key=stt_api_key
        ),
        llm=openai.LLM(
            base_url=llama_base_url,
            model=llama_model,
            api_key="no-key-needed"
        ),
        tts=openai.TTS(
            base_url=tts_base_url,
            model=tts_model,
            voice=tts_voice,
            api_key="no-key-needed"
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    agent = Assistant(
        webhook_url=webhook_url,
        webhook_enabled=webhook_enabled
    )

    await session.start(
        agent=agent,
        room=ctx.room,
    )

    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
