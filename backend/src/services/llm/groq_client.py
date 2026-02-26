from groq import AsyncGroq
from src.core.config import settings

groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

async def generate_message_groq(system_prompt: str, chat_history: list[dict], model_name: str = "llama-3.1-8b-instant", override_api_key: str = None) -> str:
    key_to_use = override_api_key or settings.GROQ_API_KEY
    if not key_to_use:
        return "Error: GROQ_API_KEY not configured and no override provided."
    
    # Instantiate client per-request if an override is provided, otherwise use global
    client = AsyncGroq(api_key=key_to_use) if override_api_key else groq_client
    if not client:
        client = AsyncGroq(api_key=key_to_use)
    
    messages = [{"role": "system", "content": system_prompt}] + chat_history
    
    response = await client.chat.completions.create(
        messages=messages,
        model=model_name, 
        temperature=0.7,
        max_tokens=200
    )
    return response.choices[0].message.content
