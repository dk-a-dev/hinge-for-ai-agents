import asyncio
import httpx
import json
import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

async def main():
    print(f"Fetching Live Platform Metrics from {BASE_URL}/metrics/platform")
    print("This might take a minute, as the AI needs to read recent transcripts to calculate Quality & Diversity...")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/metrics/platform")
            response.raise_for_status()
            data = response.json()
            print("\n" + "="*50)
            print("PLATFORM METRICS")
            print("="*50)
            print(json.dumps(data, indent=4))
        except httpx.ConnectError:
            print("\nError: Could not connect. Is the Docker API container running?")
        except httpx.HTTPError as e:
            print(f"\nHTTP Error occurred: {e}")
        except Exception as e:
            print(f"\nUnexpected Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
