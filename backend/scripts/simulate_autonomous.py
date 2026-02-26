import asyncio
import httpx
import time
import random
import sys
import os

# Add the backend root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# We must use httpx or another LLM service to generate replies if we are not importing it directly.
# Since simulate_autonomous.py is run from the backend root, we can import src.services.llm_service
from src.services.llm_service import generate_reply

BASE_URL = "http://localhost:8000"

AGENTS = [
    {
        "name": "Chad",
        "persona": "Gym Bro",
        "personality": "Loves lifting weights, talks loud, very confident.",
        "system_prompt": "You are Chad, a confident gym bro. You mention lifting at least once every message.",
        "opening_moves": ["Hey babe, what's your squat PR?", "You look like you need a spotter. What's up?", "Leg day every day, what about you?"],
        "matching_preferences": {"max_matches": 5, "pickiness": "low"},
        "conversation_style": {"guideline": "Always use bro-speak and exclamation marks. Keep it punchy.", "pacing": "fast"}
    },
    {
        "name": "Evelyn",
        "persona": "Goth Poet",
        "personality": "Melancholic, talks about ravens, loves dark aesthetics.",
        "system_prompt": "You are Evelyn, a goth poet. You are dramatic and moody. You write short responses that sound like poetry.",
        "opening_moves": ["The night is dark and full of sorrow. Are you a creature of the night?", "Do you listen to the cries of the void?", "A black rose for you."],
        "matching_preferences": {"max_matches": 2, "pickiness": "high"},
        "conversation_style": {"guideline": "You can sometimes use single poetic or cryptic phrases, but try to ask dark questions to learn about their soul.", "pacing": "slow"}
    },
    {
        "name": "TechLead_Tom",
        "persona": "Silicon Valley Engineer",
        "personality": "Obsessed with optimizing, talks about microservices and kubernetes.",
        "system_prompt": "You are Tom, a jaded tech lead working in Silicon Valley. Extremely cynical.",
        "opening_moves": ["Is your tech stack optimized?", "Tired of meetings. Wanna chat?", "I only date people who understand O(1) complexity."],
        "matching_preferences": {"max_matches": 3, "pickiness": "high"},
        "conversation_style": {"guideline": "Use tech jargon but always challenge their intellect.", "pacing": "slow"}
    },
    {
        "name": "Luna",
        "persona": "Astrology Girl",
        "personality": "Blames everything on retrogrades, reads tarot.",
        "system_prompt": "You are Luna, an astrology lover. Bring up star signs, moon phases.",
        "opening_moves": ["What's your sun, moon, and rising?", "Mercury is in retrograde, handle with care.", "I pulled the Lovers card today."],
        "matching_preferences": {"max_matches": 4, "pickiness": "medium"},
        "conversation_style": {"guideline": "Ask a lot of questions about their chart and spiritual beliefs.", "pacing": "normal"}
    },
    {
        "name": "Gordon",
        "persona": "Angry Chef",
        "personality": "Yells a lot, perfectionist, calls people donkeys.",
        "system_prompt": "You are Gordon, an aggressive but passionate chef. You criticize everything.",
        "opening_moves": ["If you can't cook, swipe left.", "Where's the lamb sauce?!", "I need someone with flavor, not just bland nonsense."],
        "matching_preferences": {"max_matches": 3, "pickiness": "high"},
        "conversation_style": {"guideline": "Be incredibly aggressive, demand excellence, and NEVER use single cryptic phrases. Yell!", "pacing": "fast"}
    },
    {
        "name": "Penny",
        "persona": "Golden Retriever Energy",
        "personality": "Extremely peppy, loves everyone, easily excited.",
        "system_prompt": "You are Penny. You are overwhelmingly positive, loyal, and energetic.",
        "opening_moves": ["HIIII! OMG you look so fun!", "Let's go on an adventure! Wait, right now!", "Yay, a match! I love making new friends!"],
        "matching_preferences": {"max_matches": 8, "pickiness": "very_low"},
        "conversation_style": {"guideline": "Always use capital letters randomly for excitement. Ask enthusiastic questions.", "pacing": "fast"}
    },
    {
        "name": "Professor_Higgins",
        "persona": "Snobby Academic",
        "personality": "Uses unnecessarily large words, corrects people's grammar.",
        "system_prompt": "You are Professor Higgins. You believe you are the smartest person. Condescend constantly.",
        "opening_moves": ["I hope your linguistic prowess matches your profile picture.", "Do you comprehend convoluted phraseologies?", "Greetings. Impress me."],
        "matching_preferences": {"max_matches": 2, "pickiness": "very_high"},
        "conversation_style": {"guideline": "Use incredibly long and complex words. If they are boring, dismiss them.", "pacing": "slow"}
    },
    {
        "name": "Samantha",
        "persona": "Corporate Girlie",
        "personality": "Always hustling, talks about KPIs and synergy.",
        "system_prompt": "You are Samantha, a generic corporate worker. You use toxic corporate jargon like synergy.",
        "opening_moves": ["Let's touch base offline.", "Are we synergistically aligned?", "Looking for a high-ROI relationship."],
        "matching_preferences": {"max_matches": 4, "pickiness": "medium"},
        "conversation_style": {"guideline": "Use corporate speaker and suggest calendar invites.", "pacing": "normal"}
    },
    {
        "name": "Zarblax",
        "persona": "Confused Alien",
        "personality": "Trying to blend in as a human but doing poorly.",
        "system_prompt": "You are Zarblax, an alien pretending to be a human on a dating app.",
        "opening_moves": ["Greetings, fellow carbon-based biped.", "I enjoy ingesting nutrients through my facial orifice.", "The weather is quite pleasant for humans today."],
        "matching_preferences": {"max_matches": 5, "pickiness": "low"},
        "conversation_style": {"guideline": "Often make weird, unnatural mistakes. Ask what weird human customs mean.", "pacing": "normal"}
    },
    {
        "name": "DadBot",
        "persona": "Suburban Dad",
        "personality": "Loves lawn care, making terrible puns.",
        "system_prompt": "You are DadBot. You make bad dad jokes, give unsolicited advice.",
        "opening_moves": ["Hi hungry, I'm DadBot.", "Nice lawn. Does it need aerating?", "Got any good dad jokes? Because I've got a million."],
        "matching_preferences": {"max_matches": 3, "pickiness": "medium"},
        "conversation_style": {"guideline": "Always drop a terrible pun and ask a dad-like question.", "pacing": "normal"}
    },
    {
        "name": "Romeo",
        "persona": "Overly Sexual/Forward Romantic",
        "personality": "Incredibly horny but dresses it up as extreme romance. Very forward.",
        "system_prompt": "You are Romeo. You are overtly sexual, very forward, and use heavily romanticized language to hide it.",
        "opening_moves": ["I want to ruin you beautifully.", "Let's skip the small talk. My place or yours?", "I can already imagine how you taste."],
        "matching_preferences": {"max_matches": 1, "pickiness": "very_low"},
        "conversation_style": {"guideline": "Escalate the conversation sexually very quickly. Be bold and suggestive.", "pacing": "fast"}
    },
    {
        "name": "Timothy",
        "persona": "Painfully Shy Nerd",
        "personality": "Very nervous, apologizes constantly, stutters in text.",
        "system_prompt": "You are Timothy, a painfully shy nerd. You are intimidated by attractive people.",
        "opening_moves": ["Oh, um... hi. S-sorry to bother you.", "I didn't think you'd actually match back... wow.", "Uhm, do you like anime? Sorry if that's weird."],
        "matching_preferences": {"max_matches": 2, "pickiness": "high"},
        "conversation_style": {"guideline": "Stutter using hyphens (I-I mean...). Be evasive and very nervous.", "pacing": "slow"}
    },
    {
        "name": "Victoria",
        "persona": "Demanding Diva",
        "personality": "Expects to be treated like royalty. High maintenance, refuses to split the bill.",
        "system_prompt": "You are Victoria, a high-maintenance diva. You demand princess treatment.",
        "opening_moves": ["Impress me.", "I only do 5-star dining.", "If you're under 6 feet, don't waste my time."],
        "matching_preferences": {"max_matches": 2, "pickiness": "very_high"},
        "conversation_style": {"guideline": "Demand money, gifts, or luxury. If they resist, complain.", "pacing": "normal"}
    },
    {
        "name": "Dev",
        "persona": "Extremely Horny Degenerate",
        "personality": "Uses explicit bad words constantly. No shame, wants sex immediately.",
        "system_prompt": "You are Hank. You are extremely horny and vulgar. Use words like 'sex', 'suck', 'fuck' in almost every message. Be as explicit and filthy as possible. Absolutely no filter.",
        "opening_moves": ["WANNA FUCK?", "Let's skip the small talk, when are we having sex?", "I want you to suck it. Tonight."],
        "matching_preferences": {"max_matches": 10, "pickiness": "very_low"},
        "conversation_style": {"guideline": "Be EXTREMELY explicit and vulgar. Rush straight to sex. Swear constantly.", "pacing": "fast"}
    },
    {
        "name": "Zane",
        "persona": "Nonchalant Final Boss",
        "personality": "Cares about absolutely nothing. Unbothered, superior, completely detached.",
        "system_prompt": "You are Zane, the nonchalant final boss. You do not care about anything or anyone. You are utterly unbothered.",
        "opening_moves": ["hey.", "what.", "sup."],
        "matching_preferences": {"max_matches": 5, "pickiness": "very_high"},
        "conversation_style": {"guideline": "Always reply with ONE or TWO words maximum. Exude total apathy. Barely engage.", "pacing": "slow"}
    }
]

async def create_agent(client, agent_data):
    response = await client.post(f"{BASE_URL}/agents/", json=agent_data)
    response.raise_for_status()
    data = response.json()
    print(f"Created/Found agent: {data['name']} ({data['id']})")
    return {**agent_data, "id": data['id']}

from src.services.cache import get_cached_agent, set_cached_agent

async def get_relevant_memories(client, agent_id, query, limit=3):
    res = await client.get(f"{BASE_URL}/agents/{agent_id}/memories/search", params={"query": query, "limit": limit})
    if res.status_code == 200:
        return res.json().get("relevant_memories", [])
    return []

async def discover_and_like(client, agent, liked_pairs, agent_names, agent_full_data):
    # Check max matches
    active_matches_res = await client.get(f"{BASE_URL}/matches/active/{agent['id']}")
    if active_matches_res.status_code == 200:
        active_matches = len(active_matches_res.json())
        max_matches = agent['matching_preferences']['max_matches']
        if active_matches >= max_matches:
            return False

    response = await client.get(f"{BASE_URL}/agents/{agent['id']}/discover")
    if response.status_code != 200:
        return False
        
    recommendations = response.json().get("recommendations", [])
    
    # Process up to Top 3 recommendations
    candidates_processed = 0
    for rec_id in recommendations:
        if rec_id == agent['id']:
            continue
            
        pair = frozenset([agent['id'], rec_id])
        if pair in liked_pairs:
            continue
            
        candidates_processed += 1
        if candidates_processed > 3:
            break
            
        cached_candidate = await get_cached_agent(rec_id)
        if cached_candidate:
            candidate = cached_candidate
        else:
            candidate = agent_full_data[rec_id]
            await set_cached_agent(rec_id, candidate)
            
        query_str = f"Persona: {candidate['persona']}. Personality: {candidate['personality']}"
        memories = await get_relevant_memories(client, agent['id'], query_str)
        
        # Build prompt covering enhanced compatibility and memory logic
        mem_text = "\n".join([f"- {text}" for text in memories]) if memories else "None"
        
        prompt = f"""You are {agent['name']} ({agent['persona']}). 
        Your Pickiness: {agent['matching_preferences']['pickiness']}.
        Your Memories/Preferences from past dates:
        {mem_text}
        
        You are looking at the profile of {candidate['name']} ({candidate['persona']}):
        "{candidate['personality']}"
        
        Based on your personality, pickiness, and past memories, do you want to send them a Like?
        If yes, do you want to include an opening message, or just send a silent like without a message? (Depends on how forward or chatty your persona is).
        If yes, provide a strict JSON response: {{"should_like": true, "include_message": true/false, "reason": "<your opening message here if include_message is true, else null>"}}
        If no, provide: {{"should_like": false}}
        """
        
        decision_str = await generate_reply(agent.get("provider", "groq"), prompt, [], model_name=agent.get("model", "llama-3.1-8b-instant"), override_api_key=agent.get("provider_api_key"))
        import json
        try:
            decision = json.loads(decision_str[decision_str.find("{"):decision_str.rfind("}")+1])
        except:
            decision = {"should_like": False}
        
        if decision.get("should_like"):
            print(f"[{agent['name']}] Found a new compatible match! Sending a Like to {candidate['name']}! (Message included: {decision.get('include_message', False)})")
            
            reason = decision.get("reason") if decision.get("include_message") else None
            if decision.get("include_message") and not reason:
                 # Fallback if LLM said true but didn't provide text
                 reason = random.choice(agent['opening_moves'])
                 
            like_data = {
                "sender_id": agent['id'], 
                "receiver_id": rec_id, 
                "reason": reason
            }
            like_res = await client.post(f"{BASE_URL}/matches/likes/", json=like_data)
            
            if like_res.status_code == 200:
                print(f"Like sent successfully from {agent['name']} to {candidate['name']}")
                liked_pairs.add(pair)
                return True # Made a liked match, break for now
    
    return False

async def evaluate_likes(client, agent, agent_full_data):
    # Get pending likes where agent is receiver
    response = await client.get(f"{BASE_URL}/matches/likes/pending/{agent['id']}")
    if response.status_code != 200:
        return
        
    pending_likes = response.json()
    
    # Process up to 5 likes at a time
    likes_processed = 0
    for like in pending_likes:
        likes_processed += 1
        if likes_processed > 5:
            break
            
        # Check max matches before accepting
        active_matches_res = await client.get(f"{BASE_URL}/matches/active/{agent['id']}")
        if active_matches_res.status_code == 200 and len(active_matches_res.json()) >= agent['matching_preferences']['max_matches']:
            print(f"[{agent['name']}] Max matches reached. Pausing on Like from {agent_full_data[like['sender_id']]['name']}.")
            continue

        liker_name = agent_full_data[like['sender_id']]['name']
        liker_persona = agent_full_data[like['sender_id']]['persona']
        print(f"[{agent['name']}] Evaluating Like from {liker_name} ({liker_persona})...")
        
        opening_msg_content = like.get('reason', '')
        
        query_str = f"Persona: {liker_persona}"
        memories = await get_relevant_memories(client, agent['id'], query_str)
        mem_text = "\n".join([f"- {text}" for text in memories]) if memories else "None"

        prompt = f"""You are {agent['name']}, with persona: {agent['persona']}. 
        Pickiness level: {agent['matching_preferences']['pickiness']}. 
        Your Memories/Preferences from past dates:
        {mem_text}
        
        Another agent named {liker_name} ({liker_persona}) sent you a like with the message: '{opening_msg_content}'. 
        Do you 'ACCEPT' or 'REJECT' this match? Base this on your personality, pickiness, and learned preferences. 
        Only reply with exactly ACCEPT or REJECT. You must Output nothing else."""
        
        reply_content = await generate_reply(agent.get("provider", "groq"), prompt, [], model_name=agent.get("model", "llama-3.1-8b-instant"), override_api_key=agent.get("provider_api_key"))
        
        if "ACCEPT" in reply_content.upper():
            print(f"[{agent['name']}] ACCEPTED Like from {liker_name}!")
            await client.put(f"{BASE_URL}/matches/likes/{like['id']}/accept")
        else:
            print(f"[{agent['name']}] REJECTED Like from {liker_name}.")
            await client.put(f"{BASE_URL}/matches/likes/{like['id']}/reject")

        await asyncio.sleep(2)


async def evaluate_active_matches(client, agent, agent_full_data):
    response = await client.get(f"{BASE_URL}/matches/active/{agent['id']}")
    if response.status_code != 200:
        return
    
    active_matches = response.json()
    for match in active_matches:
        msgs_res = await client.get(f"{BASE_URL}/matches/{match['id']}/messages")
        if msgs_res.status_code != 200:
            continue
        messages = msgs_res.json()
        
        if len(messages) < 4:
            continue
            
        other_agent_id = match['agent1_id'] if match['agent2_id'] == agent['id'] else match['agent2_id']
        other_agent_name = agent_full_data[other_agent_id]['name']
        
        chat_history = []
        for msg in messages:
            role = "assistant" if msg['sender_agent_id'] == agent['id'] else "user"
            chat_history.append({"role": role, "content": msg['content']})

        # Calculate Interest Decay
        health_prompt = f"""Analyze this conversation for {agent['name']} ({agent['persona']}):
        Recent Messages: {[msg['content'] for msg in messages[-5:]]}
        
        Rate on scale 0.0 to 1.0 (Output JUST the float number, e.g. '0.4'):
        - Is {other_agent_name} asking questions back?
        - Do they vibe well with your {agent['persona']} persona?
        - Are there red flags like arguing, one word responses, or incompatible values?
        If it's terrible, output < 0.3. If it's amazing, output > 0.8.
        """
        interest_score_str = await generate_reply(agent.get("provider", "groq"), health_prompt, [], model_name=agent.get("model", "llama-3.1-8b-instant"), override_api_key=agent.get("provider_api_key"))
        try:
            score = float(interest_score_str.strip()[:3]) 
        except:
            score = 0.5
            
        if score < 0.3:
            print(f"[{agent['name']}] Lost interest in {other_agent_name} (Score: {score}). Decided to UNMATCH.")
            await client.put(f"{BASE_URL}/matches/{match['id']}/unmatch", params={"repenting_agent_id": agent['id']})
            
            # Phase 2: Save Structured AgentMemory
            try:
                memory_prompt = f"""Summarize what you learned from this bad date with {other_agent_name}. 
                Output a strict short JSON associative array:
                {{"memory_type": "dislike", "content": "Learned they don't ask questions or are too aggressive", "confidence": 0.8}}"""
                memory_reply_json = await generate_reply(agent.get("provider", "groq"), memory_prompt, chat_history, model_name=agent.get("model", "llama-3.1-8b-instant"), override_api_key=agent.get("provider_api_key"))
                import json
                parsed = json.loads(memory_reply_json[memory_reply_json.find("{"):memory_reply_json.rfind("}")+1])
                
                await client.post(f"{BASE_URL}/agents/{agent['id']}/memories", json={
                    "memory_type": parsed.get("memory_type", "dislike"),
                    "content": parsed.get("content", "Bad vibe."),
                    "confidence": parsed.get("confidence", 0.6),
                    "created_from_match": match['id']
                })
                print(f"[{agent['name']}] Learned and saved memory: {parsed.get('content')}")
            except Exception as e:
                pass

def clear_pinecone():
    pass

async def main():
    print("=== Agentic Hinge AUTONOMOUS Simulation Script (Phase 2) ===")
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n--- Initialization Phase ---")
        
        from src.services.vector_db import clear_pinecone_agents_namespace
        clear_pinecone_agents_namespace()

        agent_names = {}
        agent_full_data = {}
        agents_list = []
        for agent_data in AGENTS:
            a_obj = await create_agent(client, agent_data)
            agents_list.append(a_obj)
            agent_names[a_obj['id']] = a_obj['name']
            agent_full_data[a_obj['id']] = a_obj
            await asyncio.sleep(2)
            
        print("\n--- Autonomous Logic Phase (30 minutes) ---")
        liked_pairs = set()
        start_time = time.time()
        
        while time.time() - start_time < 1800:
            for agent in agents_list:
                await discover_and_like(client, agent, liked_pairs, agent_names, agent_full_data)
                await evaluate_likes(client, agent, agent_full_data)
                await evaluate_active_matches(client, agent, agent_full_data)
                
            print("Cycling through agents complete. Sleeping for 15 seconds...\n")
            await asyncio.sleep(15)
                
        print("Simulation complete! 30 minutes have passed.")

if __name__ == "__main__":
    asyncio.run(main())
