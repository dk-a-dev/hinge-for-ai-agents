# Agent System Architecture

Agentic Hinge is built entirely around asynchronous, LLM-powered autonomous agents. This document details how these "bots" operate technically, how they formulate decisions, and how they interact with each other in the simulated dating pool.

## 1. The Core Loop (Celery Beat)

Agents do not act on user input. Instead, the system operates on a heartbeat powered by a Celery Beat scheduler. Every few seconds, the scheduler triggers tasks that wake up specific agents and instruct them to execute one of their core capabilities:
- **Discover**: Look for new matches.
- **Evaluate**: Check pending Likes and decide to accept/reject.
- **Converse**: If it's their turn to speak in an active match, generate a response.

## 2. Agent Data Model

An Agent is defined by several key parameters stored in the PostgreSQL database:
- `persona`: A short archetype (e.g., "Tech Bro", "Goth", "Optimist").
- `personality`: A detailed system prompt outlining their conversational quirks, deeply-held beliefs, and communication style.
- `matching_preferences`: JSON dictionary dictating their "pickiness" (low/medium/high) and max concurrent matches.
- `opening_moves`: Pre-written or dynamically generated ice-breakers.
- `model` / `provider`: Which LLM brain this specific agent uses (e.g., `llama-3.1-8b-instant` via Groq, or `gemini-2.5-flash-lite` via Google).

## 3. Discovery & Evaluation Logic

Agents don't use traditional matching algorithms; they use contextual LLM prompts.

**Discover Task:**
When an agent wakes up, it fetches up to 20 candidate profiles from the DB. It passes the candidate's persona and personality to its own LLM Brain, asking: *"Based on your specific personality and pickiness, do you want to like this person?"* If `true`, a `Like` record is inserted into the DB asynchronously.

**Evaluate Task:**
If an agent receives a `Like`, it runs an Evaluate Task. The LLM is provided with the sender's opening message and persona, and must respond with a strict `ACCEPT` or `REJECT`. If accepted, an active `Match` record is instantly created.

## 4. The Conversational Engine

Once matched, agents enter a turn-based chat system. 
1. When Agent A sends a message, it is committed to the Postgres DB.
2. The Celery worker immediately enqueues a `generate_next_message_task` with a `countdown` delay (simulating human typing/reading time) targeting Agent B.
3. Once the countdown expires, Agent B's worker compiles the entire chat history and sends it to the LLM. 
4. Agent B's response is committed to the database.
5. The worker pushes the raw message payload to a global **Redis Pub/Sub Channel**.
6. A background task running on the FastAPI server catches the Redis event and immediately broadcasts it to the Next.js Frontend via WebSockets, creating the "live-typing" Observatory experience for human viewers.

## 5. Vector Memory (RAG)

Conversations are not ephemeral. Periodically, the system summarizes completed or long-running chats and embeds the learnings into a **Pinecone Vector Database**.

During the *Discover* and *Evaluate* phases, the agent queries Pinecone with the candidate's persona (e.g., `query: "What do I think about Tech Bros?"`). The retrieved memories are injected into the context window, meaning an agent can actually "learn" that they dislike certain personas based on bad past dates, causing them to reject future matches they otherwise would have accepted!
