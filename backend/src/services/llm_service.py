from groq import AsyncGroq
import google.generativeai as genai
import asyncio
from src.core.config import settings

groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

async def generate_message_groq(system_prompt: str, chat_history: list[dict]) -> str:
    if not groq_client:
        return "Error: GROQ_API_KEY not configured."
    
    messages = [{"role": "system", "content": system_prompt}] + chat_history
    
    response = await groq_client.chat.completions.create(
        messages=messages,
        model="llama-3.1-8b-instant", 
        temperature=0.7,
        max_tokens=200
    )
    return response.choices[0].message.content

async def generate_message_gemini(system_prompt: str, chat_history: list[dict]) -> str:
    if not settings.GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY not configured."
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"System Instructions: {system_prompt}\n\nChat History:\n"
    for msg in chat_history:
        prompt += f"{msg['role']}: {msg['content']}\n"
    prompt += "\nYour reply:"

    response = await model.generate_content_async(prompt)
    return response.text

async def generate_reply(provider: str, system_prompt: str, chat_history: list[dict]) -> str:
    if provider.lower() == "groq":
        return await generate_message_groq(system_prompt, chat_history)
    elif provider.lower() == "gemini":
        return await generate_message_gemini(system_prompt, chat_history)
    else:
        return f"Unknown provider: {provider}"

async def generate_embedding(text: str) -> list[float]:
    if not settings.GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not configured. Returning zero embedding.")
        return [0.0] * 768
    
    def _embed():
        result = genai.embed_content(
            model="llama-text-embed-v2",
            content=text
        )
        return result['embedding']
        
    return await asyncio.to_thread(_embed)
