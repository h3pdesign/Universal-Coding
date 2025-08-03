
# Raindrop API version
import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

RAINDROP_API_TOKEN = os.getenv("RAINDROP_API_TOKEN")
if not RAINDROP_API_TOKEN:
    raise ValueError("Missing RAINDROP_API_TOKEN in .env file.")

RAINDROP_API_URL = "https://api.raindrop.io/rest/v1/raindrops/0"  # 0 = all collections
HEADERS = {"Authorization": f"Bearer {RAINDROP_API_TOKEN}"}

def get_raindrop_stats():
    all_raindrops = {}
    total_tags = 0
    page = 0
    while True:
        params = {"perpage": 50, "page": page}
        try:
            print(f"Fetching raindrops page... page={page}")
            response = requests.get(RAINDROP_API_URL, headers=HEADERS, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            for item in data.get("items", []):
                all_raindrops[item["_id"]] = item
                tags = item.get("tags", [])
                total_tags += len(tags)
            if not data.get("items") or len(data["items"]) < 50:
                break
            page += 1
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching Raindrop articles: {str(e)}")
            return None, None, None
    return len(all_raindrops), total_tags, all_raindrops

def test_raindrop_connection():
    try:
        response = requests.get(RAINDROP_API_URL, headers=HEADERS, params={"perpage": 1}, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"Test fetch successful: Retrieved {len(data.get('items', []))} raindrop(s) on first page")
        return True
    except Exception as e:
        print(f"Test fetch failed: {str(e)}")
        return False

def main():
    if not test_raindrop_connection():
        print("Cannot proceed due to connection failure. Check credentials and try again.")
        return
    total_raindrops, total_tags, all_raindrops = get_raindrop_stats()
    if total_raindrops is not None and total_tags is not None:
        print(f"Total number of raindrops in your Raindrop account: {total_raindrops}")
        print(f"Total number of tags attached to raindrops: {total_tags}")
        avg_tags = total_tags / total_raindrops if total_raindrops > 0 else 0
        print(f"Average number of tags per raindrop: {avg_tags:.2f}")
        raindrops_with_no_tags = sum(1 for a in all_raindrops.values() if not a.get("tags"))
        print(f"Number of raindrops with no tags: {raindrops_with_no_tags}")
    else:
        print("Failed to fetch Raindrop stats. Check the error message above for details.")

if __name__ == "__main__":
    main()
