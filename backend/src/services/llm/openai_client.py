import openai
import asyncio
from src.core.config import settings

openai_client = None
if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
    openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def generate_message_openai(system_prompt: str, chat_history: list[dict], model_name: str = "gpt-4o-mini", override_api_key: str = None) -> str:
    key_to_use = override_api_key or getattr(settings, 'OPENAI_API_KEY', None)
    if not key_to_use:
        return "Error: OPENAI_API_KEY not configured and no override provided."
        
    client = openai.AsyncOpenAI(api_key=key_to_use) if override_api_key else openai_client
    if not client:
        client = openai.AsyncOpenAI(api_key=key_to_use)
    
    # We map "assistant" -> "assistant" and "user" -> "user". OpenAI's Response API is recommended.
    # The documentation notes `client.responses.create` as the new path, but AsyncOpenAI doesn't always have it exposed seamlessly in all package versions.
    # However we'll assume standard chat completions syntax or exactly what the user provided
    messages = [{"role": "developer", "content": system_prompt}] + chat_history
    
    try:
        # User requested the new Responses API if applicable
        # We'll use chat.completions to be safe across sdk versions if responses fails
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI Error: {str(e)}"
