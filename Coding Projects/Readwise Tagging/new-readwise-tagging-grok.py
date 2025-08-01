import os
import time
import logging
import sys
import requests
from typing import Dict, List, Optional, Any, Set
from dotenv import load_dotenv
from collections import defaultdict
import json

# Configure logging with file and stderr handlers
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("readwise_tagging.log")
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

READWISE_API_TOKEN = os.getenv("READWISE_API_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")  # For tag generation only

if not READWISE_API_TOKEN:
    logging.error("Missing READWISE_API_TOKEN in .env file.")
    raise ValueError("Missing READWISE_API_TOKEN in .env file.")

# --- Readwise API helpers ---

READWISE_LIST_URL = "https://readwise.io/api/v3/list/"
READWISE_SAVE_URL = "https://readwise.io/api/v3/save/"

HEADERS = {
    "Authorization": f"Token {READWISE_API_TOKEN}",
    "Content-Type": "application/json",
}


def fetch_articles_to_tag() -> Dict[int, Dict[str, Any]]:
    """
    Fetch Readwise documents with fewer than 3 tags.

    Returns:
        Dict[int, Dict[str, Any]]: Dictionary of article IDs to article data for articles with < 3 tags
    """
    logging.info("Fetching Readwise documents with fewer than 3 tags...")
    all_articles: Dict[int, Dict[str, Any]] = {}
    next_page_cursor: Optional[str] = None

    while True:
        params: Dict[str, Any] = {"withHtmlContent": "false"}
        if next_page_cursor:
            params["pageCursor"] = next_page_cursor

        try:
            response = requests.get(
                READWISE_LIST_URL, headers=HEADERS, params=params, timeout=20
            )
            response.raise_for_status()
            data = response.json()

            for doc in data.get("results", []):
                # Readwise tags are a dict (can be empty)
                tags = doc.get("tags", {})
                if len(tags) < 3:
                    all_articles[doc["id"]] = doc

            next_page_cursor = data.get("nextPageCursor")
            if not next_page_cursor:
                break

            time.sleep(1)  # Rate limiting

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching Readwise documents: {str(e)}")
            break

    logging.info(f"Fetched {len(all_articles)} articles needing tags.")
    return all_articles


def update_article_tags(article: Dict[str, Any], new_tags: List[str]) -> bool:
    """
    Update tags for a Readwise document using the save endpoint.

    Args:
        article: The article data dictionary from Readwise API
        new_tags: List of tags to apply to the article

    Returns:
        bool: True if update was successful, False otherwise
    """
    url = article.get("source_url") or article.get("url")
    if not url:
        logging.warning(f"Article {article.get('id')} missing URL, skipping.")
        return False

    payload = {
        "url": url,
        "tags": new_tags,
        "title": article.get("title", ""),
    }

    try:
        response = requests.post(
            READWISE_SAVE_URL, headers=HEADERS, json=payload, timeout=20
        )
        if response.status_code in (200, 201):
            logging.info(f"Updated tags for article {article.get('id')}: {new_tags}")
            return True
        else:
            logging.error(
                f"Failed to update tags for {url}: {response.status_code} {response.text}"
            )
            return False

    except requests.exceptions.RequestException as e:
        logging.error(f"Exception updating tags for {url}: {str(e)}")
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


def tag_articles(articles: Dict[int, Dict[str, Any]]) -> int:
    """
    Tag Readwise articles with at least 3 tags: 2 general (one-word), 1 specific (multi-word).

    Args:
        articles: Dictionary of article IDs to article data

    Returns:
        int: Count of successfully tagged articles
    """
    tagged_count = 0

    for article_id, article in articles.items():
        current_tags = list(article.get("tags", {}).keys())

        if len(current_tags) >= 3:
            logging.info(
                f"Article {article_id} already has {len(current_tags)} tags: {current_tags}. Skipping."
            )
            continue

        title = article.get("title", "")
        excerpt = article.get("summary", "")
        url = article.get("source_url") or article.get("url", "")

        logging.info(f"Processing article {article_id}: {title}")

        new_tags = generate_tags_with_grok(title, excerpt, url)

        # Merge with existing tags, ensure at least 3 unique
        final_tags = list(set(current_tags + new_tags))
        while len(final_tags) < 3:
            final_tags.append("content")

        # Update tags on Readwise
        if update_article_tags(article, final_tags):
            tagged_count += 1

        time.sleep(1)  # Rate limiting

    logging.info(f"Tagged {tagged_count} articles.")
    return tagged_count


def main() -> None:
    """Main function to run the Readwise tagging process."""
    try:
        logging.info("Script started")

        # Fetch articles to tag
        articles = fetch_articles_to_tag()
        if not articles:
            logging.warning("No articles with fewer than 3 tags found.")
            print("No articles need tagging. Verify your Readwise account.")
            return

        # Tag articles
        tagged_count = tag_articles(articles)
        print(f"Tagged {tagged_count} articles with at least 3 tags each.")

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
