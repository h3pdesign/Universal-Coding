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

READWISE_API_TOKEN = os.getenv("READWISE_API_TOKEN")
if not READWISE_API_TOKEN:
    logging.error("Missing READWISE_API_TOKEN in environment.")
    sys.exit(1)

HEADERS = {"Authorization": f"Token {READWISE_API_TOKEN}"}
READWISE_LIST_URL = "https://readwise.io/api/v3/list/"


def fetch_all_articles():
    """
    Fetch all Readwise articles with pagination.
    Returns a list of articles.
    """
    articles = []
    next_page_cursor = None
    while True:
        params = {"withHtmlContent": "false"}
        if next_page_cursor:
            params["pageCursor"] = next_page_cursor

        try:
            response = requests.get(
                READWISE_LIST_URL, headers=HEADERS, params=params, timeout=20
            )
            response.raise_for_status()
            data = response.json()
            articles.extend(data.get("results", []))
            next_page_cursor = data.get("nextPageCursor")
            if not next_page_cursor:
                break
            time.sleep(1)  # Rate limit
        except requests.RequestException as e:
            logging.error(f"Error fetching articles: {e}")
            break

    return articles


def verify_tags(articles):
    """
    Verify each article has at least 3 tags.
    Returns a tuple (total, valid_count, invalid_articles).
    """
    invalid_articles = []
    for article in articles:
        tags = article.get("tags", {})
        tag_count = len(tags)
        if tag_count < 3:
            invalid_articles.append(
                {
                    "id": article.get("id"),
                    "title": article.get("title"),
                    "tag_count": tag_count,
                    "tags": list(tags.keys()),
                }
            )

    total = len(articles)
    valid_count = total - len(invalid_articles)
    return total, valid_count, invalid_articles


def main():
    logging.info("Starting verification of Readwise tagging...")
    articles = fetch_all_articles()
    if not articles:
        logging.error("No articles found on Readwise. Aborting.")
        sys.exit(1)

    total, valid_count, invalid_articles = verify_tags(articles)

    logging.info(f"Total articles: {total}")
    logging.info(f"Articles with >= 3 tags: {valid_count}")
    logging.info(f"Articles with < 3 tags: {len(invalid_articles)}")

    if invalid_articles:
        print("\nArticles with fewer than 3 tags:")
        for art in invalid_articles:
            print(
                f"- ID: {art['id']} Title: {art['title']}\n  Tags({art['tag_count']}): {art['tags']}\n"
            )
    else:
        print("\nAll articles have 3 or more tags.")


if __name__ == "__main__":
    main()
