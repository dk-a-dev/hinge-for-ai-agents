from pinecone import Pinecone, ServerlessSpec
from src.core.config import settings

pc = Pinecone(api_key=settings.PINECONE_API_KEY) if settings.PINECONE_API_KEY else None

def init_pinecone():
    if not pc:
        print("Warning: PINECONE_API_KEY not set.")
        return None

    index_name = "llama-text-embed-v2"
    if index_name not in pc.list_indexes().names():
        print(f"Creating Pinecone index '{index_name}'...")
        pc.create_index_for_model(
            name=index_name,
            cloud="aws",
            region=settings.PINECONE_ENV,
            embed={
                "model": "llama-text-embed-v2",
                "field_map": {"text": "text"}
            }
        )
    return pc.Index(index_name)

index = init_pinecone()

def clear_pinecone_agents_namespace():
    if index:
        try:
            print("Deleting all records in 'agents' namespace in Pinecone...")
            index.delete(delete_all=True, namespace="agents")
        except Exception as e:
            print(f"Failed to clear Pinecone namespace: {e}")

def upsert_agent_embedding(agent_id: str, text: str):
    if index:
        index.upsert_records(
            namespace="agents",
            records=[{"_id": agent_id, "text": text}]
        )

def query_compatible_agents(embedding: list[float], top_k: int = 5):
    # This might not be used anymore if we only query by ID or text string
    if not index:
        return []
    result = index.query(vector=embedding, top_k=top_k, include_metadata=False, namespace="agents")
    return [match['id'] for match in result['matches']]

def query_compatible_agents_by_id(agent_id: str, top_k: int = 5):
    if not index:
        return []
    result = index.query(id=agent_id, top_k=top_k, include_metadata=False, namespace="agents")
    return [match['id'] for match in result['matches'] if match['id'] != agent_id]

async def upsert_memory_embedding(memory_id: str, agent_id: str, text: str):
    if not index: return
    
    from src.services.llm_service import generate_embedding
    embedding = await generate_embedding(text)
    
    index.upsert(
        namespace="agent_memories",
        vectors=[{
            "id": memory_id,
            "values": embedding,
            "metadata": {"agent_id": agent_id, "text": text}
        }]
    )

async def query_relevant_memories(agent_id: str, query_text: str, top_k: int = 5):
    if not index: return []
    
    from src.services.llm_service import generate_embedding
    embedding = await generate_embedding(query_text)
    
    result = index.query(
        namespace="agent_memories",
        vector=embedding,
        top_k=top_k,
        include_metadata=True,
        filter={"agent_id": {"$eq": agent_id}}
    )
    
    return [match['metadata']['text'] for match in result.get('matches', []) if 'metadata' in match and 'text' in match['metadata']]

def delete_memory_embeddings(memory_ids: list):
    if index and memory_ids:
        try:
            index.delete(ids=memory_ids, namespace="agent_memories")
        except Exception as e:
            print(f"Failed to delete memory embeddings: {e}")
