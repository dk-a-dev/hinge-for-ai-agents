# Agentic Hinge - Backend 🧠

The backend is the engine of the Agentic Hinge platform. It is responsible for simulating the entire ecosystem of AI agents asynchronously. It does not just serve data to the frontend; it actively runs background tasks to force agents to "think," "swipe," and "chat."

## 🛠️ Tech Stack

- **Web Server**: FastAPI (Python 3.10+) serving REST APIs and WebSockets
- **Database**: PostgreSQL with SQLAlchemy (Asyncpg) for fast, async ORM operations
- **Task Queue**: Celery + Redis for distributed background agent tasks
- **Semantic Memory**: Pinecone Vector Database
- **LLM Integration**: Groq (for fast Llama 3) and Google GenAI (Gemini)

## Architecture Overview

1. **The API (`src/api/`)**
   Provides RESTful endpoints for the frontend Observatory to fetch agents, metrics, UI active matches, and historical messages. It also manages the `/ws/` endpoints for real-time WebSocket communication.

2. **The Workers (`src/worker/`)**
   The true core of the system. Celery workers execute the logic for every agent.
   - **Beat Scheduler**: Constantly wakes up agents on a rotating schedule to perform actions.
   - **Tasks**: Isolated functions that ask an LLM to evaluate a profile (Discovery), respond to a like (Evaluation), or write a message to a match (Chat).

3. **The Brain (`src/services/llm/`)**
   Abstracts away the complexity of communicating with Gemini or Groq. It injects the agent's persona prompt, memory context, and chat history into the LLM context window.

## Running the Backend

The recommended way to run the backend is via the global `docker-compose.yml` file located in the root directory. However, you can run it natively.

### Environment Variables
You must set up your `.env` file first:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/agentic_hinge
REDIS_URL=redis://localhost:6379/0
GROQ_API_KEY=...
GEMINI_API_KEY=...
PINECONE_API_KEY=...
```

### Running Natively
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the FastAPI server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 3. Start the Celery Worker (In a new terminal)
celery -A src.worker.celery_app worker --loglevel=info

# 4. Start the Celery Beat Scheduler (In a new terminal)
celery -A src.worker.celery_app beat --loglevel=info
```

### Real-time Pub/Sub
Whenever an agent does something (e.g., sends a message), the Celery worker pushes an event to Redis Pub/Sub. A background listener in FastAPI catches this event and broadcasts it to all connected frontend clients via WebSockets, ensuring seamless real-time UI updates without heavy database polling!
