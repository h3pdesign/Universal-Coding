import os
import time
import logging
import sys
import json
from typing import Dict, List, Optional, Any, Set
import requests
from dotenv import load_dotenv
from collections import defaultdict
from pathlib import Path

try:
    from azure.storage.filedatalake import DataLakeServiceClient
except ImportError:
    DataLakeServiceClient = None
    logging.warning(
        "Azure Data Lake client not installed. Install 'azure-storage-file-datalake' for Azure support."
    )

# Configure logging with file and stderr handlers
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("raindrop_tagging.log")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(stream_handler)

logging.info("Logging initialized")

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)
logging.info(f"Loaded .env from: {env_path}")


RAINDROP_API_TOKEN = os.getenv("RAINDROP_API_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")  # For tag generation only

if not RAINDROP_API_TOKEN:
    logging.error("Missing RAINDROP_API_TOKEN in .env file.")
    raise ValueError("Missing RAINDROP_API_TOKEN in .env file.")

# --- Raindrop API helpers ---
RAINDROP_API_URL = "https://api.raindrop.io/rest/v1/raindrops/0"  # 0 = all collections
RAINDROP_UPDATE_URL = "https://api.raindrop.io/rest/v1/raindrop/"  # + id

HEADERS = {
    "Authorization": f"Bearer {RAINDROP_API_TOKEN}",
    "Content-Type": "application/json",
}

# --- Storage Configuration ---
LOCAL_STORAGE_PATH = Path(os.getenv("LOCAL_STORAGE_PATH", "raindrop_data"))
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING", "")
AZURE_FILESYSTEM_NAME = os.getenv("AZURE_FILESYSTEM_NAME", "raindrop")
AZURE_DIRECTORY_NAME = os.getenv("AZURE_DIRECTORY_NAME", "articles")

# Ensure local directory exists
LOCAL_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# Azure Data Lake client (initialized if available)
azure_client = None
if DataLakeServiceClient and AZURE_CONNECTION_STRING:
    try:
        azure_client = DataLakeServiceClient.from_connection_string(
            AZURE_CONNECTION_STRING
        )
        logging.info("Azure Data Lake client initialized.")
    except Exception as e:
        logging.error(f"Failed to initialize Azure Data Lake client: {str(e)}")
        azure_client = None


def save_articles_locally(articles: Dict[int, Dict[str, Any]]) -> None:
    """
    Save articles to a local JSON file.

    Args:
        articles: Dictionary of article IDs to article data
    """
    file_path = LOCAL_STORAGE_PATH / "articles.json"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=2)
        logging.info(f"Saved {len(articles)} articles to {file_path}")
    except Exception as e:
        logging.error(f"Error saving articles locally to {file_path}: {str(e)}")


def save_articles_to_azure(articles: Dict[int, Dict[str, Any]]) -> None:
    """
    Save articles to Azure Data Lake.

    Args:
        articles: Dictionary of article IDs to article data
    """
    if not azure_client:
        logging.warning("Azure Data Lake client not available. Skipping Azure save.")
        return

    try:
        file_system_client = azure_client.get_file_system_client(AZURE_FILESYSTEM_NAME)
        directory_client = file_system_client.get_directory_client(AZURE_DIRECTORY_NAME)
        file_client = directory_client.get_file_client("articles.json")

        articles_data = json.dumps(articles, indent=2).encode("utf-8")
        file_client.upload_data(articles_data, overwrite=True)
        logging.info(
            f"Saved {len(articles)} articles to Azure Data Lake at {AZURE_FILESYSTEM_NAME}/{AZURE_DIRECTORY_NAME}/articles.json"
        )
    except Exception as e:
        logging.error(f"Error saving articles to Azure Data Lake: {str(e)}")


def load_articles_locally() -> Optional[Dict[int, Dict[str, Any]]]:
    """
    Load articles from a local JSON file.

    Returns:
        Optional[Dict[int, Dict[str, Any]]]: Loaded articles dictionary or None if not found/error
    """
    file_path = LOCAL_STORAGE_PATH / "articles.json"
    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                articles = json.load(f)
            logging.info(f"Loaded {len(articles)} articles from {file_path}")
            return articles
    except Exception as e:
        logging.error(f"Error loading articles locally from {file_path}: {str(e)}")
    return None


def load_articles_from_azure() -> Optional[Dict[int, Dict[str, Any]]]:
    """
    Load articles from Azure Data Lake.

    Returns:
        Optional[Dict[int, Dict[str, Any]]]: Loaded articles dictionary or None if not found/error
    """
    if not azure_client:
        logging.warning("Azure Data Lake client not available. Skipping Azure load.")
        return None

    try:
        file_system_client = azure_client.get_file_system_client(AZURE_FILESYSTEM_NAME)
        directory_client = file_system_client.get_directory_client(AZURE_DIRECTORY_NAME)
        file_client = directory_client.get_file_client("articles.json")

        download = file_client.download_file()
        articles_data = download.readall().decode("utf-8")
        articles = json.loads(articles_data)
        logging.info(f"Loaded {len(articles)} articles from Azure Data Lake")
        return articles
    except Exception as e:
        logging.error(f"Error loading articles from Azure Data Lake: {str(e)}")
        return None


def fetch_raindrops_to_tag() -> Dict[int, Dict[str, Any]]:
    """
    Fetch Raindrop articles with fewer than 3 tags.
    Also saves fetched articles to local and Azure storage.

    Returns:
        Dict[int, Dict[str, Any]]: Dictionary of raindrop IDs to raindrop data for items with < 3 tags
    """
    logging.info("Fetching Raindrop articles with fewer than 3 tags...")
    all_raindrops: Dict[int, Dict[str, Any]] = {}
    page = 0
    while True:
        params = {"perpage": 50, "page": page}
        try:
            response = requests.get(RAINDROP_API_URL, headers=HEADERS, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            for item in data.get("items", []):
                tags = item.get("tags", [])
                if len(tags) < 3:
                    all_raindrops[item["_id"]] = item
            if not data.get("items") or len(data["items"]) < 50:
                break
            page += 1
            time.sleep(1)
        except Exception as e:
            logging.error(f"Error fetching Raindrop articles: {str(e)}")
            break
    logging.info(f"Fetched {len(all_raindrops)} raindrops needing tags.")
    # Save fetched raindrops to storage
    if all_raindrops:
        save_articles_locally(all_raindrops)
        save_articles_to_azure(all_raindrops)
    return all_raindrops


def update_raindrop_tags(raindrop: Dict[str, Any], new_tags: List[str]) -> bool:
    """
    Update tags for a Raindrop article using the update endpoint.

    Args:
        raindrop: The raindrop data dictionary from Raindrop API
        new_tags: List of tags to apply to the raindrop

    Returns:
        bool: True if update was successful, False otherwise
    """
    raindrop_id = raindrop.get("_id")
    if not raindrop_id:
        logging.warning(f"Raindrop missing _id, skipping.")
        return False

    payload = {
        "tags": new_tags,
    }

    try:
        response = requests.put(
            RAINDROP_UPDATE_URL + str(raindrop_id), headers=HEADERS, json=payload, timeout=20
        )
        if response.status_code in (200, 201):
            logging.info(f"Updated tags for raindrop {raindrop_id}: {new_tags}")
            return True
        else:
            logging.error(
                f"Failed to update tags for raindrop {raindrop_id}: {response.status_code} {response.text}"
            )
            return False

    except requests.exceptions.RequestException as e:
        logging.error(f"Exception updating tags for raindrop {raindrop_id}: {str(e)}")
        return False


# --- Tag Generation (Grok or fallback) ---
def generate_tags_with_grok(title: str, excerpt: str, url: str) -> List[str]:
    """
    Generate tags using xAI Grok API based on article content.
    Falls back to simulation on API failure.

    Args:
        title: Article title
        excerpt: Article excerpt or summary
        url: Article URL

    Returns:
        List[str]: List of generated tags (at least 3)
    """
    content = f"{title} {excerpt}"
    tags: List[str] = []
    grok_api_key = GROK_API_KEY

    if grok_api_key:
        try:
            endpoint = "https://api.xai.com/v1/generate"
            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "grok-1",
                "prompt": f"Generate up to 3 relevant tags for the following article content: {content[:500]}...",
                "max_tokens": 50,
                "temperature": 0.7,
            }
            response = requests.post(
                endpoint, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            generated_text = data.get("choices", [{}])[0].get("text", "").strip()
            tags = [tag.strip() for tag in generated_text.split(",") if tag.strip()]

            if not tags:
                logging.warning(f"No tags generated by Grok API for '{title}'.")
            else:
                logging.info(f"Grok API generated tags for '{title}': {tags}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Grok API call failed for '{title}': {str(e)}")
            time.sleep(1)
    else:
        logging.warning(
            "GROK_API_KEY not found in environment variables. Falling back to simulation."
        )

    # Fallback to rule-based tag generation if no tags from API
    if not tags:
        logging.info(f"Falling back to rule-based tag generation for '{title}'.")
        tags = generate_fallback_tags(content)
        logging.info(f"Generated fallback tags for '{title}': {tags}")

    return tags


def generate_fallback_tags(content: str) -> List[str]:
    """
    Generate tags based on content keywords when API fails.

    Args:
        content: The article content (title + excerpt)

    Returns:
        List[str]: List of generated tags (at least 3)
    """
    content_lower = content.lower()
    general_tags: Set[str] = set()
    specific_tag = ""

    # Determine general tags based on content keywords
    if any(
        word in content_lower for word in ["news", "politics", "election", "government"]
    ):
        general_tags.update(["news", "politics"])
    elif any(
        word in content_lower for word in ["tech", "technology", "ai", "software"]
    ):
        general_tags.update(["tech", "innovation"])
    elif any(word in content_lower for word in ["science", "research", "study"]):
        general_tags.update(["science", "research"])
    elif any(
        word in content_lower for word in ["health", "medicine", "disease", "wellness"]
    ):
        general_tags.update(["health", "wellness"])
    elif any(
        word in content_lower for word in ["finance", "economy", "money", "market"]
    ):
        general_tags.update(["finance", "economy"])
    elif any(
        word in content_lower
        for word in ["education", "learning", "school", "university"]
    ):
        general_tags.update(["education", "learning"])
    elif any(
        word in content_lower for word in ["entertainment", "movie", "music", "game"]
    ):
        general_tags.update(["entertainment", "media"])
    else:
        general_tags.update(["information", "content"])

    # Determine a specific, multi-word tag
    if "ai" in content_lower or "artificial intelligence" in content_lower:
        specific_tag = "artificial intelligence"
    elif "climate" in content_lower or "environment" in content_lower:
        specific_tag = "climate change"
    elif "design" in content_lower or "apple" in content_lower:
        specific_tag = "product design"
    elif "healthcare" in content_lower or "hospital" in content_lower:
        specific_tag = "healthcare industry"
    elif "stock" in content_lower or "investment" in content_lower:
        specific_tag = "financial markets"
    elif "student" in content_lower:
        specific_tag = "educational resources"
    elif "movie" in content_lower or "film" in content_lower:
        specific_tag = "film industry"
    else:
        specific_tag = "relevant subject"

    tags = list(general_tags)[:2] + [specific_tag]
    tags = list(set(tags))  # Remove duplicates

    # Ensure we have at least 3 tags
    while len(tags) < 3:
        fallback_tags = ["other content", "miscellaneous", "general topic"]
        for ft in fallback_tags:
            if ft not in tags and len(tags) < 3:
                tags.append(ft)

    return tags


def tag_raindrops(raindrops: Dict[int, Dict[str, Any]]) -> int:
    """
    Tag Raindrop articles with at least 3 tags: 2 general (one-word), 1 specific (multi-word).

    Args:
        raindrops: Dictionary of raindrop IDs to raindrop data

    Returns:
        int: Count of successfully tagged raindrops
    """
    tagged_count = 0

    for raindrop_id, raindrop in raindrops.items():
        current_tags = raindrop.get("tags", [])

        if len(current_tags) >= 3:
            logging.info(
                f"Raindrop {raindrop_id} already has {len(current_tags)} tags: {current_tags}. Skipping."
            )
            continue

        title = raindrop.get("title", "")
        excerpt = raindrop.get("excerpt", "")

        logging.info(f"Processing raindrop {raindrop_id}: {title}")

        new_tags = generate_tags_with_grok(title, excerpt, raindrop.get("link", ""))

        # Merge with existing tags, ensure at least 3 unique
        final_tags = list(set(current_tags + new_tags))
        while len(final_tags) < 3:
            final_tags.append("content")

        # Update tags on Raindrop
        if update_raindrop_tags(raindrop, final_tags):
            tagged_count += 1

        time.sleep(1)  # Rate limiting

    logging.info(f"Tagged {tagged_count} raindrops.")
    return tagged_count


def main() -> None:
    """Main function to run the Raindrop tagging process."""
    try:
        logging.info("Script started")

        # Try loading raindrops from storage first (optional, depending on use case)
        raindrops = load_articles_from_azure()
        if not raindrops:
            raindrops = load_articles_locally()
        if not raindrops:
            # Fetch raindrops to tag from Raindrop API if not in storage
            raindrops = fetch_raindrops_to_tag()
        if not raindrops:
            logging.warning("No raindrops with fewer than 3 tags found.")
            print("No raindrops need tagging. Verify your Raindrop account.")
            return

        # Tag raindrops
        tagged_count = tag_raindrops(raindrops)
        print(f"Tagged {tagged_count} raindrops with at least 3 tags each.")

        logging.info("Script finished")
        print("Script finished")

    except KeyboardInterrupt:
        logging.info("Script interrupted by user")
        print("Script stopped by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
