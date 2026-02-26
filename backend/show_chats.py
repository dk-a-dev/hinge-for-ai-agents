import asyncio
import os
import sys

# Add the backend directory to sys.path so we can import src modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import pool

from src.core.config import settings
from src.models.domain import Match, Message, Agent

async def main():
    print(f"Connecting to database at: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    LocalSession = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    try:
        async with LocalSession() as session:
            print("Fetching matches...")
            # Get all matches
            stmt = select(Match)
            result = await session.execute(stmt)
            matches = result.scalars().all()

            if not matches:
                print("No matches found in the database yet.")
                return

            print(f"Found {len(matches)} matches.")
            
            for match in matches:
                # get agents
                agent1_stmt = select(Agent).where(Agent.id == match.agent1_id)
                agent2_stmt = select(Agent).where(Agent.id == match.agent2_id)
                
                agent1_res = await session.execute(agent1_stmt)
                agent2_res = await session.execute(agent2_stmt)
                
                agent1 = agent1_res.scalar_one_or_none()
                agent2 = agent2_res.scalar_one_or_none()
                
                name1 = agent1.name if agent1 else match.agent1_id
                name2 = agent2.name if agent2 else match.agent2_id

                print(f"\n{'='*60}")
                print(f"Match between {name1} and {name2} (Match ID: {match.id})")
                print(f"{'='*60}")

                # get messages
                msgs_stmt = select(Message).where(Message.match_id == match.id).order_by(Message.created_at)
                msgs_res = await session.execute(msgs_stmt)
                messages = msgs_res.scalars().all()

                if not messages:
                    print("  [No messages yet]")
                    continue

                for msg in messages:
                    sender_name = name1 if msg.sender_agent_id == match.agent1_id else name2
                    print(f"[{sender_name}]: {msg.content}")

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
