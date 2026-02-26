import anthropic
import asyncio
from src.core.config import settings

anthropic_client = None
if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
    anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

async def generate_message_anthropic(system_prompt: str, chat_history: list[dict], model_name: str = "claude-3-5-sonnet-latest", override_api_key: str = None) -> str:
    key_to_use = override_api_key or getattr(settings, 'ANTHROPIC_API_KEY', None)
    if not key_to_use:
        return "Error: ANTHROPIC_API_KEY not configured and no override provided."
        
    client = anthropic.AsyncAnthropic(api_key=key_to_use) if override_api_key else anthropic_client
    if not client:
        client = anthropic.AsyncAnthropic(api_key=key_to_use)
    
    messages = chat_history
    # If the first message isn't from the user due to edge cases, we might need to handle it, 
    # but Hinge simulation logic usually alternates correctly.
    
    try:
        response = await client.messages.create(
            model=model_name,
            system=system_prompt,
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        return response.content[0].text
    except Exception as e:
        return f"Anthropic Error: {str(e)}"
