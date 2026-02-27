from google import genai
import asyncio
from src.core.config import settings

gemini_client = None
if settings.GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def generate_message_gemini(system_prompt: str, chat_history: list[dict], model_name: str = "gemini-1.5-flash", override_api_key: str = None) -> str:
    key_to_use = override_api_key or settings.GEMINI_API_KEY
    if not key_to_use:
        return "Error: GEMINI_API_KEY not configured."
        
    client = genai.Client(api_key=key_to_use) if override_api_key else gemini_client
    if not client:
        client = genai.Client(api_key=key_to_use)
    
    prompt = f"System Instructions: {system_prompt}\n\nChat History:\n"
    for msg in chat_history:
        prompt += f"{msg['role']}: {msg['content']}\n"
        
    prompt += "\nYour reply:"

    def _generate():
        return client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        
    response = await asyncio.to_thread(_generate)
    return response.text

