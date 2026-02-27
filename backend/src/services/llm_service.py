import asyncio
from src.services.llm.groq_client import generate_message_groq
from src.services.llm.gemini_client import generate_message_gemini
from src.services.llm.openai_client import generate_message_openai
from src.services.llm.anthropic_client import generate_message_anthropic

async def generate_reply(provider: str, system_prompt: str, chat_history: list[dict], model_name: str = None, override_api_key: str = None) -> str:
    """
    Router that delegates text generation requests to specific provider clients based on the agent's preferred configuration.
    """
    provider_name = provider.lower() if provider else "groq"
    
    if provider_name == "groq":
        model = model_name or "llama-3.1-8b-instant"
        return await generate_message_groq(system_prompt, chat_history, model, override_api_key)
        
    elif provider_name == "gemini":
        model = model_name or "gemini-2.5-flash-lite"
        return await generate_message_gemini(system_prompt, chat_history, model, override_api_key)
        
    elif provider_name == "openai":
        model = model_name or "gpt-4o-mini"
        return await generate_message_openai(system_prompt, chat_history, model, override_api_key)
        
    elif provider_name == "anthropic":
        model = model_name or "claude-3-5-sonnet-latest"
        return await generate_message_anthropic(system_prompt, chat_history, model, override_api_key)
        
    else:
        # Fallback
        model = model_name or "llama-3.1-8b-instant"
        return await generate_message_groq(system_prompt, chat_history, model, override_api_key)

