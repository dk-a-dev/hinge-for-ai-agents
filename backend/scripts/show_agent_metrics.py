import asyncio
import httpx
import json
import argparse
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

async def main(agent_id):
    if not agent_id:
        print("Please provide an agent ID, e.g. python show_agent_metrics.py <agent_id>")
        return

    print(f"Fetching Metrics for Agent {agent_id} from {BASE_URL}/metrics/agent/{agent_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/metrics/agent/{agent_id}")
            response.raise_for_status()
            data = response.json()
            print("\n" + "="*50)
            print("AGENT METRICS")
            print("="*50)
            print(json.dumps(data, indent=4))
        except httpx.ConnectError:
            print("\nError: Could not connect. Is the Docker API container running?")
        except httpx.HTTPError as e:
            print(f"\nHTTP Error occurred: {e}")
        except Exception as e:
            print(f"\nUnexpected Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch metrics for a specific Agent")
    parser.add_argument("agent_id", type=str, help="The UUID of the agent")
    args = parser.parse_args()
    
    asyncio.run(main(args.agent_id))
