
# Raindrop API version
import os
import sys
import time
import logging
import requests
from dotenv import load_dotenv

# Setup logging to stderr
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stderr,
)

# Load environment variables from .env
load_dotenv()

RAINDROP_API_TOKEN = os.getenv("RAINDROP_API_TOKEN")
if not RAINDROP_API_TOKEN:
    logging.error("Missing RAINDROP_API_TOKEN in environment.")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {RAINDROP_API_TOKEN}"}
RAINDROP_API_URL = "https://api.raindrop.io/rest/v1/raindrops/0"

def fetch_all_raindrops():
    """
    Fetch all Raindrop articles with pagination.
    Returns a list of raindrops.
    """
    raindrops = []
    page = 0
    while True:
        params = {"perpage": 50, "page": page}
        try:
            response = requests.get(
                RAINDROP_API_URL, headers=HEADERS, params=params, timeout=20
            )
            response.raise_for_status()
            data = response.json()
            raindrops.extend(data.get("items", []))
            if not data.get("items") or len(data["items"]) < 50:
                break
            page += 1
            time.sleep(1)  # Rate limit
        except requests.RequestException as e:
            logging.error(f"Error fetching raindrops: {e}")
            break
    return raindrops

def verify_tags(raindrops):
    """
    Verify each raindrop has at least 3 tags.
    Returns a tuple (total, valid_count, invalid_raindrops).
    """
    invalid_raindrops = []
    for item in raindrops:
        tags = item.get("tags", [])
        tag_count = len(tags)
        if tag_count < 3:
            invalid_raindrops.append(
                {
                    "id": item.get("_id"),
                    "title": item.get("title"),
                    "tag_count": tag_count,
                    "tags": tags,
                }
            )
    total = len(raindrops)
    valid_count = total - len(invalid_raindrops)
    return total, valid_count, invalid_raindrops

def main():
    logging.info("Starting verification of Raindrop tagging...")
    raindrops = fetch_all_raindrops()
    if not raindrops:
        logging.error("No raindrops found on Raindrop. Aborting.")
        sys.exit(1)

    total, valid_count, invalid_raindrops = verify_tags(raindrops)

    logging.info(f"Total raindrops: {total}")
    logging.info(f"Raindrops with >= 3 tags: {valid_count}")
    logging.info(f"Raindrops with < 3 tags: {len(invalid_raindrops)}")

    if invalid_raindrops:
        print("\nRaindrops with fewer than 3 tags:")
        for art in invalid_raindrops:
            print(
                f"- ID: {art['id']} Title: {art['title']}\n  Tags({art['tag_count']}): {art['tags']}\n"
            )
    else:
        print("\nAll raindrops have 3 or more tags.")

if __name__ == "__main__":
    main()
