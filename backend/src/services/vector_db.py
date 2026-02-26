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
